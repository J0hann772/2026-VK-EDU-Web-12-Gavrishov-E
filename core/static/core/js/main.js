function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showAjaxError(message) {
    const errorBox = document.getElementById('ajax-error-box');
    if (errorBox) {
        errorBox.textContent = message;
        errorBox.classList.remove('d-none');
        window.clearTimeout(errorBox._hideTimer);
        errorBox._hideTimer = window.setTimeout(() => {
            errorBox.classList.add('d-none');
        }, 5000);
    } else {
        alert(message);
    }
}

async function sendPost(url, params) {
    const csrfToken = getCookie('csrftoken');
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'X-CSRFToken': csrfToken || '',
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: new URLSearchParams(params),
    });

    let data = {};
    try {
        data = await response.json();
    } catch (e) {
        data = { error: 'Сервер вернул некорректный ответ (проверьте CSRF или метод запроса).' };
    }

    return { ok: response.ok, status: response.status, data };
}

document.addEventListener('DOMContentLoaded', () => {
    // Лайки и дизлайки вопросов и ответов
    document.querySelectorAll('.js-vote-btn').forEach((button) => {
        button.addEventListener('click', async () => {
            const box = button.closest('.js-vote-box');
            const ratingInput = box.querySelector('.js-rating-input');
            const url = button.dataset.url;
            const paramName = button.dataset.param;
            const objectId = button.dataset.objectId;
            const value = button.dataset.value;

            try {
                const { ok, status, data } = await sendPost(url, {
                    [paramName]: objectId,
                    value: value,
                });

                if (status === 401 && data.login_url) {
                    showAjaxError(data.error || 'Необходимо войти в аккаунт.');
                    const nextUrl = encodeURIComponent(window.location.pathname + window.location.search);
                    window.location.href = `${data.login_url}?next=${nextUrl}`;
                    return;
                }

                if (!ok) {
                    showAjaxError(data.error || 'Не удалось сохранить оценку.');
                    return;
                }

                ratingInput.value = data.rating;
                const upBtn = box.querySelector('.spin-up');
                const downBtn = box.querySelector('.spin-down');

                if (data.user_vote === 1) {
                    upBtn.disabled = true;
                    upBtn.classList.add('active-vote');
                    upBtn.title = 'Вы уже поставили лайк';
                    downBtn.disabled = false;
                    downBtn.classList.remove('active-vote');
                    downBtn.title = 'Поставить дизлайк';
                } else if (data.user_vote === -1) {
                    downBtn.disabled = true;
                    downBtn.classList.add('active-vote');
                    downBtn.title = 'Вы уже поставили дизлайк';
                    upBtn.disabled = false;
                    upBtn.classList.remove('active-vote');
                    upBtn.title = 'Поставить лайк';
                }
            } catch (err) {
                showAjaxError('Ошибка сети при отправке оценки.');
            }
        });
    });

    // Отметка правильного ответа автором вопроса
    document.querySelectorAll('.js-correct-checkbox').forEach((checkbox) => {
        checkbox.addEventListener('change', async () => {
            const url = checkbox.dataset.url;
            const questionId = checkbox.dataset.questionId;
            const answerId = checkbox.dataset.answerId;
            const previousState = !checkbox.checked;

            try {
                const { ok, status, data } = await sendPost(url, {
                    question_id: questionId,
                    answer_id: answerId,
                });

                if (status === 401 && data.login_url) {
                    checkbox.checked = previousState;
                    showAjaxError(data.error || 'Необходимо войти в аккаунт.');
                    const nextUrl = encodeURIComponent(window.location.pathname + window.location.search);
                    window.location.href = `${data.login_url}?next=${nextUrl}`;
                    return;
                }

                if (!ok) {
                    checkbox.checked = previousState;
                    showAjaxError(data.error || 'Не удалось изменить статус ответа.');
                    return;
                }

                checkbox.checked = Boolean(data.is_correct);
            } catch (err) {
                checkbox.checked = previousState;
                showAjaxError('Ошибка сети при изменении статуса ответа.');
            }
        });
    });
});
