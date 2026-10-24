
"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("asset-submission-form");
    const fileInput = document.getElementById("file-upload-input");
    const dropzone = document.getElementById("upload-dropzone");
    const selectedFileName = document.getElementById("selected-file-name");
    const submitButton = document.getElementById("scan-submit-button");
    const errorElement = document.getElementById("submission-error");
    const resultsSection = document.getElementById("compliance-results");
    const summaryElement = document.getElementById("compliance-summary");
    const detailsElement = document.getElementById("compliance-details");

    const brandIdInput = document.getElementById("active-brand-id");
    const campaignInput = document.getElementById("campaign-name");
    const channelInput = document.getElementById("target-channel");

    if (
        !form ||
        !fileInput ||
        !submitButton ||
        !resultsSection ||
        !summaryElement ||
        !detailsElement
    ) {
        console.error(
            "BrandVerify: Required submission page elements were not found."
        );
        return;
    }

    const MAX_FILE_SIZE = 100 * 1024 * 1024;

    const AUDIO_EXTENSIONS = new Set([
        ".wav",
        ".mp3",
        ".m4a",
        ".aac",
        ".ogg",
        ".flac"
    ]);

    const VIDEO_EXTENSIONS = new Set([
        ".mp4",
        ".mov",
        ".mkv",
        ".avi",
        ".mpeg",
        ".mpg"
    ]);

    // WEBM can be either audio or video, so determine its type from the MIME
    // type where possible.
    const WEBM_EXTENSION = ".webm";

    function getExtension(filename) {
        const lastDot = filename.lastIndexOf(".");

        if (lastDot === -1) {
            return "";
        }

        return filename.slice(lastDot).toLowerCase();
    }

    function getMediaType(file) {
        const extension = getExtension(file.name);

        if (AUDIO_EXTENSIONS.has(extension)) {
            return "audio";
        }

        if (VIDEO_EXTENSIONS.has(extension)) {
            return "video";
        }

        if (extension === WEBM_EXTENSION) {
            if (file.type.startsWith("audio/")) {
                return "audio";
            }

            if (file.type.startsWith("video/")) {
                return "video";
            }

            return null;
        }

        return null;
    }

    function showError(message) {
        if (!errorElement) {
            window.alert(message);
            return;
        }

        errorElement.textContent = message;
        errorElement.hidden = false;
    }

    function clearError() {
        if (errorElement) {
            errorElement.textContent = "";
            errorElement.hidden = true;
        }
    }

    function setLoading(isLoading) {
        submitButton.disabled = isLoading;

        if (isLoading) {
            submitButton.dataset.originalText =
                submitButton.textContent.trim();

            submitButton.textContent = "Scanning media...";
            form.setAttribute("aria-busy", "true");
        } else {
            submitButton.textContent =
                submitButton.dataset.originalText ||
                "Run Compliance Scan";

            form.removeAttribute("aria-busy");
        }
    }

    function createElement(tagName, className, text) {
        const element = document.createElement(tagName);

        if (className) {
            element.className = className;
        }

        if (text !== undefined && text !== null) {
            // Use textContent, never innerHTML, for backend/user-provided text.
            element.textContent = String(text);
        }

        return element;
    }

    function addSectionHeading(parent, heading) {
        parent.appendChild(createElement("h3", "", heading));
    }

    function formatStatus(status) {
        if (typeof status !== "string" || !status.trim()) {
            return "review_required";
        }

        return status.trim().toLowerCase().replace(/[\s-]+/g, "_");
    }

    function statusLabel(status) {
        const labels = {
            pass: "PASS",
            fail: "FAIL",
            review_required: "REVIEW REQUIRED",
            review: "REVIEW REQUIRED",
            error: "ERROR"
        };

        return labels[status] || status.replace(/_/g, " ").toUpperCase();
    }

    function renderStatus(parent, status) {
        const normalized = formatStatus(status);
        const statusElement = createElement(
            "span",
            "compliance-status status-" + normalized,
            statusLabel(normalized)
        );

        parent.appendChild(statusElement);
    }

    function displayValue(value) {
        if (value === null || value === undefined || value === "") {
            return "Not provided";
        }

        if (typeof value === "string" || typeof value === "number") {
            return String(value);
        }

        try {
            return JSON.stringify(value, null, 2);
        } catch {
            return String(value);
        }
    }

    function renderFinding(parent, finding, index) {
        const card = createElement("article", "compliance-finding");

        if (typeof finding === "string") {
            card.appendChild(
                createElement("p", "", finding)
            );

            parent.appendChild(card);
            return;
        }

        if (!finding || typeof finding !== "object") {
            card.appendChild(
                createElement("p", "", displayValue(finding))
            );

            parent.appendChild(card);
            return;
        }

        const title =
            finding.title ||
            finding.rule ||
            finding.category ||
            finding.check ||
            `Finding ${index + 1}`;

        card.appendChild(createElement("h4", "", title));

        const findingStatus =
            finding.status ||
            finding.severity ||
            finding.result;

        if (findingStatus) {
            const statusLine = createElement("p");
            statusLine.appendChild(
                createElement("strong", "", "Status: ")
            );
            statusLine.appendChild(
                document.createTextNode(displayValue(findingStatus))
            );
            card.appendChild(statusLine);
        }

        const message =
            finding.message ||
            finding.description ||
            finding.reason ||
            finding.finding;

        if (message) {
            card.appendChild(
                createElement("p", "", message)
            );
        }

        const suggestion =
            finding.suggestion ||
            finding.recommendation ||
            finding.remediation;

        if (suggestion) {
            const suggestionLine = createElement("p");
            suggestionLine.appendChild(
                createElement("strong", "", "Suggested action: ")
            );
            suggestionLine.appendChild(
                document.createTextNode(displayValue(suggestion))
            );
            card.appendChild(suggestionLine);
        }

        parent.appendChild(card);
    }

    function renderFindings(parent, findings) {
        if (
            !Array.isArray(findings) ||
            findings.length === 0
        ) {
            parent.appendChild(
                createElement(
                    "p",
                    "",
                    "No individual findings were returned by the backend."
                )
            );
            return;
        }

        findings.forEach((finding, index) => {
            renderFinding(parent, finding, index);
        });
    }

    function renderTranscript(parent, transcript) {
        if (
            transcript === undefined ||
            transcript === null ||
            transcript === ""
        ) {
            return;
        }

        const section = createElement("div", "result-section");
        addSectionHeading(section, "Transcription");

        section.appendChild(
            createElement("div", "transcript-box", transcript)
        );

        parent.appendChild(section);
    }

    function renderFrameColors(parent, data) {
        const colors =
            data.sampled_frame_colors ||
            data.frame_colors ||
            data.sampled_colors ||
            data.detected_colors;

        if (!Array.isArray(colors) || colors.length === 0) {
            return;
        }

        const section = createElement("div", "result-section");
        addSectionHeading(section, "Sampled Video Frame Colors");

        const list = document.createElement("ul");

        colors.forEach((color) => {
            const item = document.createElement("li");
            item.textContent = displayValue(color);
            list.appendChild(item);
        });

        section.appendChild(list);
        parent.appendChild(section);
    }

    function renderResults(data, mediaType) {
        detailsElement.replaceChildren();
        summaryElement.replaceChildren();

        const status = formatStatus(data.status);

        renderStatus(summaryElement, status);

        const description = createElement(
            "p",
            "",
            mediaType === "audio"
                ? "Audio compliance scan completed."
                : "Video compliance scan completed."
        );

        summaryElement.appendChild(description);

        const campaignName = campaignInput?.value.trim();
        const targetChannel = channelInput?.value;

        if (campaignName) {
            detailsElement.appendChild(
                createElement(
                    "p",
                    "",
                    "Campaign: " + campaignName
                )
            );
        }

        if (targetChannel) {
            detailsElement.appendChild(
                createElement(
                    "p",
                    "",
                    "Publishing channel: " + targetChannel
                )
            );
        }

        const findingsSection = createElement(
            "div",
            "result-section"
        );

        addSectionHeading(findingsSection, "Findings");

        renderFindings(
            findingsSection,
            data.findings
        );

        detailsElement.appendChild(findingsSection);

        renderTranscript(detailsElement, data.transcript);

        if (mediaType === "video") {
            renderFrameColors(detailsElement, data);
        }

        if (data.note) {
            const noteSection = createElement(
                "div",
                "result-note"
            );

            noteSection.appendChild(
                createElement("strong", "", "Note: ")
            );

            noteSection.appendChild(
                document.createTextNode(displayValue(data.note))
            );

            detailsElement.appendChild(noteSection);
        }

        resultsSection.hidden = false;
        resultsSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }

    async function readApiResponse(response) {
        const contentType =
            response.headers.get("content-type") || "";

        if (contentType.includes("application/json")) {
            return await response.json();
        }

        const text = await response.text();

        return {
            detail: text || "The server returned an empty response."
        };
    }

    function getErrorMessage(data, response) {
        if (data && typeof data.detail === "string") {
            return data.detail;
        }

        if (Array.isArray(data?.detail)) {
            return data.detail
                .map((item) => item.msg || displayValue(item))
                .join("; ");
        }

        if (data && typeof data.message === "string") {
            return data.message;
        }

        if (response.status === 404) {
            return "The compliance endpoint was not found. Check that the router is included in backend/main.py.";
        }

        if (response.status === 409) {
            return "No approved rules were found for this brand. Verify the brand ID and that its rules are approved.";
        }

        if (response.status === 413) {
            return "The uploaded file is too large.";
        }

        if (response.status === 422) {
            return "The server rejected the submitted data. Check the brand ID and upload fields.";
        }

        if (response.status >= 500) {
            return "The backend encountered an error while processing the media. Check your terminal for the server traceback.";
        }

        return `The scan failed with HTTP status ${response.status}.`;
    }

    // Clicking the upload area opens the file picker.
    if (dropzone) {
        dropzone.addEventListener("click", (event) => {
            if (event.target === fileInput) {
                return;
            }

            fileInput.click();
        });

        dropzone.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                fileInput.click();
            }
        });

        dropzone.addEventListener("dragover", (event) => {
            event.preventDefault();
            dropzone.classList.add("drag-over");
        });

        dropzone.addEventListener("dragleave", () => {
            dropzone.classList.remove("drag-over");
        });

        dropzone.addEventListener("drop", (event) => {
            event.preventDefault();
            dropzone.classList.remove("drag-over");

            const files = event.dataTransfer?.files;

            if (!files || files.length === 0) {
                return;
            }

            // Assigning a FileList is not supported in every browser.
            // DataTransfer provides a compatible FileList in modern browsers.
            try {
                const transfer = new DataTransfer();
                transfer.items.add(files[0]);
                fileInput.files = transfer.files;
                updateSelectedFile();
            } catch (error) {
                console.error("Unable to attach the dropped file:", error);
                showError("Could not select the dropped file. Please use the file picker.");
            }
        });
    }

    function updateSelectedFile() {
        clearError();

        const file = fileInput.files?.[0];

        if (!file) {
            if (selectedFileName) {
                selectedFileName.textContent = "No file selected";
            }
            return;
        }

        if (selectedFileName) {
            selectedFileName.textContent =
                `${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
        }

        const mediaType = getMediaType(file);

        if (!mediaType) {
            showError(
                "Unsupported file type. Please upload a supported audio or video file."
            );
        } else if (file.size > MAX_FILE_SIZE) {
            showError("The file exceeds the 100 MB upload limit.");
        }
    }

    fileInput.addEventListener("change", updateSelectedFile);

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        clearError();

        const brandId = brandIdInput?.value.trim();
        const file = fileInput.files?.[0];

        if (!brandId) {
            showError(
                "The active brand ID is missing. Set it to the actual brand ID used by your backend."
            );
            return;
        }

        if (!file) {
            showError("Please select an audio or video file first.");
            return;
        }

        const mediaType = getMediaType(file);

        if (!mediaType) {
            showError(
                "Unsupported file type. Upload a supported audio or video file."
            );
            return;
        }

        if (file.size === 0) {
            showError("The selected file is empty. Please choose another file.");
            return;
        }

        if (file.size > MAX_FILE_SIZE) {
            showError("The file exceeds the 100 MB upload limit.");
            return;
        }

        // These endpoints match the FastAPI routes described in your backend:
        // POST /api/compliance/audio
        // POST /api/compliance/video
        const endpoint =
            mediaType === "audio"
                ? "/api/media/audio/scan"
                : "/api/media/video/scan";

        const formData = new FormData();

        

        formData.append("file", file);

        if (mediaType === "audio") {
            formData.append("target_lufs", "-24.0");
            formData.append("tolerance_lu", "1.0");
        }

        if (mediaType === "video") {
            const disclaimer = document.getElementById("required-disclaimer");

            if (!disclaimer || !disclaimer.value.trim()) {
                showError("Please enter the required disclaimer for the video.");
                setLoading(false);
                return;
            }

            formData.append("required_disclaimer", disclaimer.value.trim());
            formData.append("target_lufs", "-24.0");
            formData.append("tolerance_lu", "1.0");
        }

        setLoading(true);
        resultsSection.hidden = true;

        try {
            const response = await fetch(endpoint, {
                method: "POST",
                body: formData
            });

            const data = await readApiResponse(response);

            if (!response.ok) {
                throw new Error(
                    getErrorMessage(data, response)
                );
            }

            renderResults(data, mediaType);
        } catch (error) {
            console.error("BrandVerify compliance scan error:", error);

            showError(
                error instanceof TypeError
                    ? "Could not connect to the backend. Open this page through your FastAPI server and check that it is running."
                    : error.message || "An unexpected error occurred during the scan."
            );
        } finally {
            setLoading(false);
        }
    });
});
