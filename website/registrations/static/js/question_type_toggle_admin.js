document.addEventListener("DOMContentLoaded", () => {
    function ensureFollowUpQuestionExists(choiceTbody, followUpPanel) {
        const followUpGroup = followUpPanel?.querySelector(
            ".inline-group[data-inline-model='registrations-question']"
        );
        if (!followUpGroup) return;

        const existingFollowUpRows = followUpGroup.querySelectorAll(
            "tbody[data-inline-model='registrations-question']:not(.djn-empty-form)"
        );
        if (existingFollowUpRows.length > 0) return;

        if (choiceTbody.dataset.autoAddingFollowUp === "true") return;

        const addFollowUpLink = followUpGroup.querySelector(
            "a.djn-add-handler.djn-model-registrations-question"
        );
        if (!addFollowUpLink) return;

        choiceTbody.dataset.autoAddingFollowUp = "true";
        addFollowUpLink.click();

        setTimeout(() => {
            choiceTbody.dataset.autoAddingFollowUp = "false";
        }, 0);
    }

    function validateQuestionRow(questionTbody) {
        
        const questionType = questionTbody.querySelector("select[name$='-question_type']")?.value;

        const choicesPanel = questionTbody.querySelector("tr.djn-tr:not(.form-row)");

        const isMulti = questionType === "multi";
        const isChoice = questionType === "choice";
        const isDropdown = questionType === "dropdown";
        const isTextList = questionType === "textlist";
        const isChoiceList = questionType === "choicelist";
        const isFollowUp = isFollowUpTbody(questionTbody);

        [
            questionTbody.querySelector("td.field-min_choices"),
            questionTbody.querySelector("td.field-max_choices"),
            questionTbody.querySelector("td.field-warnings"),
        ].forEach(td => {
            if (td) td.style.visibility = isMulti || isTextList || isChoiceList ? "visible" : "hidden";
        });

        const parentChoiceTd = questionTbody.querySelector("td.field-parent_choice");
        if (parentChoiceTd) {
            parentChoiceTd.style.display = isFollowUp ? "" : "none";
        }

        if (choicesPanel) {
            choicesPanel.style.display = (isMulti || isChoice || isDropdown || isTextList || isChoiceList) ? "" : "none";
        }
    }

    function validateChoiceRow(choiceTbody) {

        const followUpCheckBox = choiceTbody.querySelector("input[name$='-follow_up']");
        const followUpPanel = choiceTbody.querySelector("tr.djn-tr:not(.form-row)");
        const followUpTd = choiceTbody.querySelector("td.field-follow_up");

        const parentQuestionTbody = choiceTbody.closest("tbody[data-inline-model='registrations-question']");
        const questionType = parentQuestionTbody?.querySelector("select[name$='-question_type']")?.value;

        const isChoice = questionType === "choice";
        const parentIsFollowUp = isFollowUpTbody(parentQuestionTbody);

        if (followUpTd) {
            followUpTd.style.visibility = (isChoice && !parentIsFollowUp) ? "visible" : "hidden";
        }

        if (followUpCheckBox && followUpPanel) {
            if (followUpCheckBox.checked) {
                ensureFollowUpQuestionExists(choiceTbody, followUpPanel);
            }
            followUpPanel.style.display = followUpCheckBox.checked ? "" : "none";
        }
    }

    function isFollowUpTbody(tbody) {
        return tbody.id.includes("follow_up_questions");
    }

    function getQuestionTbody(el) {
        const tbody = el.closest("tbody[data-inline-model='registrations-question']");
        if (!tbody || tbody.id.includes("empty")) return null;
        return tbody;
    }

    function getChoiceTbody(el) {
        const tbody = el.closest("tbody[data-inline-model='registrations-questionchoice']");
        if (!tbody || tbody.id.includes("empty")) return null;
        return tbody;
    }

    function attachListeners() {
        if (document.body.dataset.questionTypeToggleDelegated === "true") {
            return;
        }

        document.body.dataset.questionTypeToggleDelegated = "true";

        document.addEventListener("change", event => {
            const target = event.target;
            if (!(target instanceof HTMLElement)) return;

            if (target.matches("select[name$='-question_type']")) {
                const tbody = getQuestionTbody(target);
                if (tbody) validateQuestionRow(tbody);
            }

            if (target.matches("input[name$='-follow_up']")) {
                const tbody = getChoiceTbody(target);
                if (tbody) validateChoiceRow(tbody);
            }
        });
    }

    function initAll() {
        document.querySelectorAll("tbody[data-inline-model='registrations-question']").forEach(tbody => {
            if (!tbody.id.includes("empty")) {
                validateQuestionRow(tbody);
            }
        });

        document.querySelectorAll("tbody[data-inline-model='registrations-questionchoice']").forEach(tbody => {
            if (!tbody.id.includes("empty")) {
                validateChoiceRow(tbody);
            }
        });

        attachListeners();
    }

    const observer = new MutationObserver(() => {
        attachListeners();

        document.querySelectorAll("tbody[data-inline-model='registrations-question']").forEach(tbody => {
            if (!tbody.dataset.initialized && !tbody.id.includes("empty")) {
                    tbody.dataset.initialized = "true";
                    validateQuestionRow(tbody);
                }
            }
        );

        document.querySelectorAll("tbody[data-inline-model='registrations-questionchoice']").forEach(tbody => {
            if (!tbody.dataset.initialized && !tbody.id.includes("empty")) {
                tbody.dataset.followUpInitialized = "true";
                validateChoiceRow(tbody);
            }
        });
    });

    observer.observe(document.body, { childList: true, subtree: true });

    initAll();
});