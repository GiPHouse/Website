document.addEventListener("DOMContentLoaded", () => {
    function validateFollowUpRow(el) {
        const wrapper = el.closest(".mb-3");

        if (!isFollowUpQuestion(el)) return;

        const parentQuestionId = el.getAttribute("parent-question-id");
        const parentChoiceId = el.getAttribute("parent-choice-id");
        const parent = document.querySelector(`[question-id="${parentQuestionId}"]`);
        
        if (!parent) return;

        const parentAnswer = getAnswer(parent)
        
        wrapper.style.display = (parentAnswer === parentChoiceId) ? "" : "none";
    }
    
    function isFollowUpQuestion(el) {
        return el.hasAttribute("parent-question-id")
    }

    function getAnswer(el) {
        return el.querySelector(`input:checked`)?.value;
    }

    function attachListeners() {
        document.addEventListener("change", event => {
            const target = event.target;
            if (!(target instanceof HTMLElement)) return;

            const questionEl = target.closest("[question-id]");
            if (!questionEl) return;

            const questionId = questionEl.getAttribute("question-id");

            document.querySelectorAll(`[parent-question-id="${questionId}"]`).forEach(validateFollowUpRow);
        });
    }

    function initAll() {
        document.querySelectorAll("[parent-question-id]").forEach(el => {
            validateFollowUpRow(el);
        });

        attachListeners();
    }

    const observer = new MutationObserver(() => {
        attachListeners();
        document.querySelectorAll("[parent-question-id]").forEach(el => {
            validateFollowUpRow(el);
        });
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
    
    initAll();
});