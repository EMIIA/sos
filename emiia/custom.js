document.addEventListener('DOMContentLoaded', function() {
    console.log("EMIIA.AI Scripts loaded...");

    // === НАСТРОЙКИ IOT ===
    const iotUrl = 'https://sos.emiia.ai/vv1.html';
    const itemName = 'EMIIA.AI IOT';

    // === 1. ЛОГИКА IOT В МЕНЮ ===
    function addIotItem(container) {
        if (container.querySelector('[data-iot-item="true"]')) return;
        let listWrapper = container.querySelector('div > div');
        if (!listWrapper) listWrapper = container;
        if (listWrapper.querySelectorAll('button').length === 0) return;

        const itemHtml = `
        <div class="flex" data-iot-item="true">
            <button class="flex w-full justify-between gap-2 items-center px-3 py-1.5 text-sm cursor-pointer rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800/50" type="button" title="Операционное пространство">
                <div class="flex-1 truncate">
                    <div class="flex flex-1 gap-2 items-center">
                        <div class="shrink-0">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 16 16" stroke="currentColor" stroke-width="1" class="size-4" style="color: #6d9eeb;">
                                <path d="M14 4.577v6.846L8 15l-6-3.577V4.577L8 1l6 3.577zM8.5.134a1 1 0 0 0-1 0l-6 3.577a1 1 0 0 0-.5.866v6.846a1 1 0 0 0 .5.866l6 3.577a1 1 0 0 0 1 0l6-3.577a1 1 0 0 0 .5-.866V4.577a1 1 0 0 0-.5-.866L8.5.134z"/>
                            </svg>
                        </div>
                        <div class="truncate">${itemName}</div>
                    </div>
                </div>
                <div class="shrink-0">
                    <div class="flex">
                        <div class="flex h-[1.125rem] min-h-[1.125rem] w-8 shrink-0 cursor-pointer items-center rounded-full px-1 mx-[1px] transition bg-gray-200 dark:bg-transparent border border-gray-300 dark:border-gray-600" role="switch" aria-checked="false" data-iot-switch="true">
                            <span class="pointer-events-none block size-3 shrink-0 rounded-full bg-white shadow-mini transition-transform duration-200" style="transform: translateX(0px);"></span>
                        </div>
                    </div>
                </div>
            </button>
        </div>`;

        listWrapper.insertAdjacentHTML('beforeend', itemHtml);
        const newItem = listWrapper.querySelector('[data-iot-item="true"] button');
        if (typeof tippy === 'function') tippy(newItem, { content: 'Операционное пространство', placement: 'top' });

        newItem.addEventListener('click', (e) => {
            e.preventDefault();
            const track = newItem.querySelector('[data-iot-switch="true"]');
            const thumb = track.querySelector('span');
            track.style.backgroundColor = '#3d85c6';
            track.style.borderColor = '#3d85c6';
            thumb.style.transform = 'translateX(12px)';
            track.setAttribute('aria-checked', 'true');
            setTimeout(() => { window.location.href = iotUrl; }, 300);
        });
    }

    // === 2. ЛОГИКА ДОБАВЛЕНИЯ КНОПОК (ПОСЛЕ ВВОДА) ===
    function addActionButtons() {
        // Ищем блок "Предложено" (по тексту заголовка или иконке)
        // Open WebUI часто меняет структуру, поэтому ищем надежно
        const suggestedHeaders = document.querySelectorAll('.text-xs.font-medium');
        let suggestedHeader = null;
        
        suggestedHeaders.forEach(h => {
            if (h.innerText.includes("Предложено")) suggestedHeader = h;
        });

        if (!suggestedHeader) return;
        
        // Находим контейнер, в котором лежит "Предложено" (обычно это родитель-обертка)
        // Нам нужно вставить кнопки ПЕРЕД этим заголовком, но внутри общего контейнера, чтобы они исчезали вместе.
        // Обычно структура: Container -> Header ("Предложено") -> List
        const parentContainer = suggestedHeader.parentElement; // Это может быть div с padding
        
        // Проверяем, не добавили ли мы уже
        if (parentContainer.parentElement.querySelector('.emii-action-buttons-container')) return;

        const buttonsHtml = `
        <div class="emii-action-buttons-container">
            <div class="emii-scroll-container">
                <div class="emii-buttons-wrapper">
                    
                    <button class="emii-action-btn emii-btn-free-tier">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M6.428 1.151C6.708.591 7.213 0 8 0s1.292.592 1.572 1.151C9.861 1.73 10 2.431 10 3v3.691l5.17 2.585a1.5 1.5 0 0 1 .83 1.342V12a.5.5 0 0 1-.582.493l-5.507-.918-.375 2.253 1.318 1.318A.5.5 0 0 1 10.5 16h-5a.5.5 0 0 1-.354-.854l1.319-1.318-.376-2.253-5.507.918A.5.5 0 0 1 0 12v-1.382a1.5 1.5 0 0 1 .83-1.342L6 6.691V3c0-.568.14-1.271.428-1.849m.894.448C7.111 2.02 7 2.569 7 3v4a.5.5 0 0 1-.276.447l-5.448 2.724a.5.5 0 0 0-.276.447v.792l5.418-.903a.5.5 0 0 1 .575.41l.5 3a.5.5 0 0 1-.14.437L6.708 15h2.586l-.647-.646a.5.5 0 0 1-.14-.436l.5-3a.5.5 0 0 1 .576-.411L15 11.41v-.792a.5.5 0 0 0-.276-.447L9.276 7.447A.5.5 0 0 1 9 7V3c0-.432-.11-.979-.322-1.401C8.458 1.159 8.213 1 8 1s-.458.158-.678.599"/>
                        </svg>
                        <span>Free Tier</span>
                    </button>

                    <button class="emii-action-btn">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M6 1v3H1V1zM1 0a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h5a1 1 0 0 0 1-1V1a1 1 0 0 0-1-1zm14 12v3h-5v-3zm-5-1a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h5a1 1 0 0 0 1-1v-3a1 1 0 0 0-1-1zM6 8v7H1V8zM1 7a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h5a1 1 0 0 0 1-1V8a1 1 0 0 0-1-1zm14-6v7h-5V1zm-5-1a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h5a1 1 0 0 0 1-1V1a1 1 0 0 0-1-1z"/>
                        </svg>
                        <span>Операционное пространство</span>
                    </button>

                    <button class="emii-action-btn">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 16.875h3.375m0 0h3.375m-3.375 0V13.5m0 3.375v3.375M6 10.5h2.25a2.25 2.25 0 0 0 2.25-2.25V6a2.25 2.25 0 0 0-2.25-2.25H6A2.25 2.25 0 0 0 3.75 6v2.25A2.25 2.25 0 0 0 6 10.5Zm0 9.75h2.25A2.25 2.25 0 0 0 10.5 18v-2.25a2.25 2.25 0 0 0-2.25-2.25H6a2.25 2.25 0 0 0-2.25 2.25V18A2.25 2.25 0 0 0 6 20.25Zm9.75-9.75H18a2.25 2.25 0 0 0 2.25-2.25V6A2.25 2.25 0 0 0 18 3.75h-2.25A2.25 2.25 0 0 0 13.5 6v2.25a2.25 2.25 0 0 0 2.25 2.25Z"/>
                        </svg>
                        <span>Рабочее пространство</span>
                    </button>

                    <button class="emii-action-btn">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M8 0q-.264 0-.523.017l.064.998a7 7 0 0 1 .918 0l.064-.998A8 8 0 0 0 8 0M6.44.152q-.52.104-1.012.27l.321.948q.43-.147.884-.237L6.44.153zm4.132.271a8 8 0 0 0-1.011-.27l-.194.98q.453.09.884.237zm1.873.925a8 8 0 0 0-.906-.524l-.443.896q.413.205.793.459zM4.46.824q-.471.233-.905.524l.556.83a7 7 0 0 1 .793-.458zM2.725 1.985q-.394.346-.74.74l.752.66q.303-.345.648-.648zm11.29.74a8 8 0 0 0-.74-.74l-.66.752q.346.303.648.648zm1.161 1.735a8 8 0 0 0-.524-.905l-.83.556q.254.38.458.793l.896-.443zM1.348 3.555q-.292.433-.524.906l.896.443q.205-.413.459-.793zM.423 5.428a8 8 0 0 0-.27 1.011l.98.194q.09-.453.237-.884zM15.848 6.44a8 8 0 0 0-.27-1.012l-.948.321q.147.43.237.884zM.017 7.477a8 8 0 0 0 0 1.046l.998-.064a7 7 0 0 1 0-.918zM16 8a8 8 0 0 0-.017-.523l-.998.064a7 7 0 0 1 0 .918l.998.064A8 8 0 0 0 16 8M.152 9.56q.104.52.27 1.012l.948-.321a7 7 0 0 1-.237-.884l-.98.194zm15.425 1.012q.168-.493.27-1.011l-.98-.194q-.09.453-.237.884zM.824 11.54a8 8 0 0 0 .524.905l.83-.556a7 7 0 0 1-.458-.793zm13.828.905q.292-.434.524-.906l-.896-.443q-.205.413-.459.793zm-12.667.83q.346.394.74.74l.66-.752a7 7 0 0 1-.648-.648zm11.29.74q.394-.346.74-.74l-.752-.66q-.302.346-.648.648zm-1.735 1.161q.471-.233.905-.524l-.556-.83a7 7 0 0 1-.793.458zm-7.985-.524q.434.292.906.524l.443-.896a7 7 0 0 1-.793-.459zm1.873.925q.493.168 1.011.27l.194-.98a7 7 0 0 1-.884-.237zm4.132.271a8 8 0 0 0 1.012-.27l-.321-.948a7 7 0 0 1-.884.237l.194.98zm-2.083.135a8 8 0 0 0 1.046 0l-.064-.998a7 7 0 0 1-.918 0zM8.5 4.5a.5.5 0 0 0-1 0v3h-3a.5.5 0 0 0 0 1h3v3a.5.5 0 0 0 1 0v-3h3a.5.5 0 0 0 0-1h-3z"/>
                        </svg>
                        <span>Субагенты</span>
                    </button>

                    <button class="emii-action-btn">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path fill-rule="evenodd" d="M8.646 5.646a.5.5 0 0 1 .708 0l2 2a.5.5 0 0 1 0 .708l-2 2a.5.5 0 0 1-.708-.708L10.293 8 8.646 6.354a.5.5 0 0 1 0-.708m-1.292 0a.5.5 0 0 0-.708 0l-2 2a.5.5 0 0 0 0 .708l2 2a.5.5 0 0 0 .708-.708L5.707 8l1.647-1.646a.5.5 0 0 0 0-.708"/>
                            <path d="M3 0h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2v-1h1v1a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v1H1V2a2 2 0 0 1 2-2"/>
                            <path d="M1 5v-.5a.5.5 0 0 1 1 0V5h.5a.5.5 0 0 1 0 1h-2a.5.5 0 0 1 0-1zm0 3v-.5a.5.5 0 0 1 1 0V8h.5a.5.5 0 0 1 0 1h-2a.5.5 0 0 1 0-1zm0 3v-.5a.5.5 0 0 1 1 0v.5h.5a.5.5 0 0 1 0 1h-2a.5.5 0 0 1 0-1z"/>
                        </svg>
                        <span>Новые функции</span>
                    </button>

                </div>
            </div>
        </div>`;

        // Вставляем перед заголовком "Предложено"
        suggestedHeader.insertAdjacentHTML('beforebegin', buttonsHtml);
        console.log("EMIIA.AI: Action buttons added.");
    }

    // === ГЛОБАЛЬНЫЙ НАБЛЮДАТЕЛЬ ===
    const observer = new MutationObserver(() => {
        // Поиск меню интеграций
        document.querySelectorAll('.min-w-70').forEach(el => addIotItem(el));
        // Поиск блока предложений
        addActionButtons();
    });

    observer.observe(document.body, { childList: true, subtree: true });
    
    // Первичный запуск
    addActionButtons();
});

// Скрытие блока
function hideBottomBlock() {
  document.querySelectorAll('div').forEach(div => {
    const text = div.textContent.trim();
    
    // Только блоки, где текст начинается с EMIIA.AI — скрываем
    if (text.startsWith('EMIIA.AI (Open WebUI) ‧ v0.9.1') && div.className.includes('svelte-')) {
      div.style.display = 'none';
    }
  });
}

hideBottomBlock();
const observer = new MutationObserver(hideBottomBlock);
observer.observe(document.body, { childList: true, subtree: true, characterData: true });
