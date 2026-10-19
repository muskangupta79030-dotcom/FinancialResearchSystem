const API = "http://127.0.0.1:8000";


// ======================================================
// BASIC HELPERS
// ======================================================

function $(id) {
    return document.getElementById(id);
}


function show(element) {
    if (element) {
        element.classList.remove("hidden");
    }
}


function hide(element) {
    if (element) {
        element.classList.add("hidden");
    }
}


function escapeHTML(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function showLoading(title = "Processing...", text = "Please wait while the agent pipeline runs.") {

    $("loadingTitle").textContent = title;
    $("loadingText").textContent = text;

    show($("loadingOverlay"));
}


function hideLoading() {
    hide($("loadingOverlay"));
}


function showAlert(message) {

    $("alertText").textContent = message;

    show($("alertBox"));

    setTimeout(() => {
        hide($("alertBox"));
    }, 5000);
}


$("closeAlert").addEventListener("click", () => {
    hide($("alertBox"));
});


// ======================================================
// NAVIGATION
// ======================================================

const sectionTitles = {
    dashboard: "Dashboard",
    documents: "Documents",
    research: "Research Assistant",
    comparison: "Comparison",
    report: "Financial Report"
};


function openSection(sectionId) {

    document.querySelectorAll(".section").forEach(section => {
        section.classList.remove("active");
    });

    document.querySelectorAll(".nav-item").forEach(button => {
        button.classList.remove("active");
    });

    const section = $(sectionId);

    if (section) {
        section.classList.add("active");
    }

    const navButton = document.querySelector(
        `.nav-item[data-section="${sectionId}"]`
    );

    if (navButton) {
        navButton.classList.add("active");
    }

    $("pageTitle").textContent =
        sectionTitles[sectionId] || "Dashboard";

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


document.querySelectorAll(".nav-item").forEach(button => {

    button.addEventListener("click", () => {

        const sectionId = button.dataset.section;

        openSection(sectionId);

    });

});


document.querySelectorAll("[data-go]").forEach(button => {

    button.addEventListener("click", () => {

        const sectionId = button.dataset.go;

        openSection(sectionId);

    });

});


// ======================================================
// BACKEND STATUS
// ======================================================

async function checkBackend() {

    try {

        const response = await fetch(API + "/", {
            method: "GET"
        });

        if (!response.ok) {
            throw new Error("Backend unavailable");
        }

        const data = await response.json();

        $("backendStatus").textContent = "Backend Online";

        $("statusDot").classList.remove("offline");
        $("statusDot").classList.add("online");

        return data;

    } catch (error) {

        $("backendStatus").textContent = "Backend Offline";

        $("statusDot").classList.remove("online");
        $("statusDot").classList.add("offline");

        return null;
    }
}


checkBackend();


// ======================================================
// LOAD SEED DOCUMENTS
// ======================================================

$("seedBtn").addEventListener("click", async () => {

    showLoading(
        "Loading Seed Documents",
        "Preparing financial documents for research..."
    );

    try {

        const response = await fetch(
            API + "/seed-documents/load",
            {
                method: "POST"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Failed to load seed documents."
            );
        }

        showAlert(
            data.message ||
            "Seed documents loaded successfully."
        );

        await checkBackend();

    } catch (error) {

        showAlert(
            "Seed document loading failed: " +
            error.message
        );

    } finally {

        hideLoading();

    }

});


// ======================================================
// FILE UPLOAD
// ======================================================

let selectedFile = null;


const fileInput = $("fileInput");
const dropZone = $("dropZone");
const processBtn = $("processBtn");


fileInput.addEventListener("change", event => {

    const file = event.target.files[0];

    if (!file) {
        return;
    }

    handleSelectedFile(file);

});


function handleSelectedFile(file) {

    if (
        file.type !== "application/pdf" &&
        !file.name.toLowerCase().endsWith(".pdf")
    ) {

        showAlert("Please select a PDF file.");

        selectedFile = null;

        $("selectedFile").textContent =
            "No file selected";

        processBtn.disabled = true;

        return;
    }


    selectedFile = file;

    $("selectedFile").textContent =
        `${file.name} (${formatFileSize(file.size)})`;

    processBtn.disabled = false;

}


function formatFileSize(bytes) {

    if (bytes === 0) {
        return "0 Bytes";
    }

    const units = [
        "Bytes",
        "KB",
        "MB",
        "GB"
    ];

    const index = Math.floor(
        Math.log(bytes) / Math.log(1024)
    );

    return (
        parseFloat(
            (bytes / Math.pow(1024, index)).toFixed(2)
        )
        + " "
        + units[index]
    );
}


// ======================================================
// DRAG AND DROP
// ======================================================

dropZone.addEventListener("dragover", event => {

    event.preventDefault();

    dropZone.classList.add("dragover");

});


dropZone.addEventListener("dragleave", () => {

    dropZone.classList.remove("dragover");

});


dropZone.addEventListener("drop", event => {

    event.preventDefault();

    dropZone.classList.remove("dragover");

    const files = event.dataTransfer.files;

    if (!files || files.length === 0) {
        return;
    }

    handleSelectedFile(files[0]);

});


// ======================================================
// DOCUMENT PROCESSING
// ======================================================

processBtn.addEventListener("click", async () => {

    if (!selectedFile) {

        showAlert("Please select a PDF first.");

        return;
    }


    const formData = new FormData();

    formData.append(
        "file",
        selectedFile
    );


    showLoading(
        "Processing Financial Document",
        "Running Document, Extraction, Red Flag, Embedding and Vector Database agents..."
    );


    try {

        const response = await fetch(
            API + "/documents/upload",
            {
                method: "POST",
                body: formData
            }
        );


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.message ||
                "Document processing failed."
            );

        }


        displayDocumentResult(data);

        showAlert(
            "Document processed successfully."
        );


    } catch (error) {

        showAlert(
            "Document processing failed: " +
            error.message
        );

    } finally {

        hideLoading();

    }

});


// ======================================================
// DISPLAY DOCUMENT RESULT
// ======================================================

function displayDocumentResult(data) {

    show($("documentResult"));


    // Filename

    $("resultFilename").textContent =
        data.filename || "Financial Document";


    // Pipeline

    displayPipeline(
        data.pipeline || []
    );


    // Metrics

    const metrics =
        data.extracted_metrics || {};


    $("metricRevenue").textContent =
        getMetricValue(
            metrics,
            [
                "revenue",
                "net_sales",
                "total_sales"
            ]
        );


    $("metricNetIncome").textContent =
        getMetricValue(
            metrics,
            [
                "net_income",
                "net_profit",
                "profit_after_tax"
            ]
        );


    $("metricOperatingIncome").textContent =
        getMetricValue(
            metrics,
            [
                "operating_income",
                "operating_profit"
            ]
        );


    // Red Flags

    displayRedFlags(
        data.red_flag_analysis
    );


    // Risk badge

    displayRisk(
        data.red_flag_analysis
    );


    // Processing details

    displayProcessingDetails(
        data.document_processing
    );

}


function displayPipeline(pipeline) {

    const container =
        $("pipelineResult");

    if (!pipeline.length) {

        container.innerHTML =
            `<p class="empty-state">
                No pipeline information available.
            </p>`;

        return;
    }


    container.innerHTML =
        pipeline.map(item => {

            return `
                <div class="pipeline-result-item success">
                    <strong>✓ ${escapeHTML(item)}</strong>
                </div>
            `;

        }).join("");

}


function getMetricValue(metrics, keys) {

    for (const key of keys) {

        if (
            metrics[key] !== undefined &&
            metrics[key] !== null &&
            metrics[key] !== ""
        ) {

            const value = metrics[key];

            if (
                typeof value === "object" &&
                value !== null
            ) {

                if (value.value !== undefined) {
                    return value.value;
                }

                if (value.amount !== undefined) {
                    return value.amount;
                }
            }

            return value;
        }

    }

    return "—";
}


// ======================================================
// RED FLAG DISPLAY
// ======================================================

function displayRedFlags(analysis) {

    const container =
        $("redFlags");


    if (!analysis) {

        container.innerHTML =
            `<div class="no-flags">
                No red-flag analysis available.
            </div>`;

        return;
    }


    let flags = [];


    if (Array.isArray(analysis)) {

        flags = analysis;

    } else if (
        Array.isArray(analysis.flags)
    ) {

        flags = analysis.flags;

    } else if (
        Array.isArray(analysis.red_flags)
    ) {

        flags = analysis.red_flags;

    }


    if (flags.length === 0) {

        container.innerHTML =
            `<div class="no-flags">
                No major financial red flags were identified
                by the current automated analysis.
            </div>`;

        return;
    }


    container.innerHTML =
        flags.map(flag => {

            if (typeof flag === "string") {

                return `
                    <div class="flag-card medium">
                        <strong>Potential Indicator</strong>
                        <p>${escapeHTML(flag)}</p>
                    </div>
                `;

            }


            const severity =
                String(
                    flag.severity ||
                    flag.level ||
                    "Medium"
                ).toLowerCase();


            return `
                <div class="flag-card ${escapeHTML(severity)}">

                    <strong>
                        ${escapeHTML(
                            flag.title ||
                            flag.type ||
                            flag.name ||
                            "Potential Financial Indicator"
                        )}
                    </strong>

                    <p>
                        ${escapeHTML(
                            flag.description ||
                            flag.message ||
                            flag.details ||
                            flag.reason ||
                            "Potential financial indicator detected."
                        )}
                    </p>

                </div>
            `;

        }).join("");

}


function displayRisk(analysis) {

    const badge =
        $("riskBadge");


    let risk = "Low";


    if (analysis) {

        risk =
            analysis.overall_risk ||
            analysis.risk_level ||
            analysis.overallRisk ||
            analysis.risk ||
            "Low";

    }


    risk =
        String(risk)
            .replace("_", " ")
            .trim();


    badge.textContent =
        "Risk: " + risk;


    badge.classList.remove(
        "risk-low",
        "risk-medium",
        "risk-high"
    );


    const normalized =
        risk.toLowerCase();


    if (normalized.includes("high")) {

        badge.classList.add("risk-high");

    } else if (
        normalized.includes("medium")
    ) {

        badge.classList.add("risk-medium");

    } else {

        badge.classList.add("risk-low");

    }

}


function displayProcessingDetails(details) {

    const container =
        $("processingDetails");


    if (!details) {

        container.innerHTML =
            `<p class="empty-state">
                Processing details unavailable.
            </p>`;

        return;
    }


    const rows = [

        [
            "Total Characters",
            details.total_characters
        ],

        [
            "Total Chunks",
            details.total_chunks
        ],

        [
            "Embedding Count",
            details.embedding_count
        ],

        [
            "Embedding Dimension",
            details.embedding_dimension
        ],

        [
            "Stored in Vector Database",
            details.stored_in_vector_database
        ]

    ];


    container.innerHTML =
        rows.map(row => {

            return `
                <div class="detail-row">

                    <span>
                        ${escapeHTML(row[0])}
                    </span>

                    <span>
                        ${escapeHTML(
                            row[1] === undefined ||
                            row[1] === null
                                ? "—"
                                : row[1]
                        )}
                    </span>

                </div>
            `;

        }).join("");

}


// ======================================================
// RESEARCH ASSISTANT
// ======================================================

$("researchForm").addEventListener(
    "submit",
    async event => {

        event.preventDefault();


        const input =
            $("researchInput");

        const query =
            input.value.trim();


        if (!query) {

            showAlert(
                "Please enter a research question."
            );

            return;
        }


        addChatMessage(
            "user",
            query
        );


        input.value = "";


        showLoading(
            "Researching Financial Documents",
            "Searching the indexed financial knowledge base..."
        );


        try {

            const params =
                new URLSearchParams({

                    query: query,

                    top_k: "5"

                });


            const response =
                await fetch(
                    API +
                    "/research?" +
                    params.toString(),
                    {
                        method: "POST"
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    data.message ||
                    "Research request failed."
                );

            }


            if (
                data.status === "no_results"
            ) {

                addChatMessage(
                    "assistant",
                    data.message ||
                    "No relevant information was found in the indexed documents."
                );

                displaySources([]);

                return;
            }


            addChatMessage(
                "assistant",
                data.answer ||
                "No answer was generated."
            );


            displaySources(
                data.sources || []
            );


        } catch (error) {

            addChatMessage(
                "assistant",
                "Sorry, I could not process your request.\n\n" +
                error.message
            );


            showAlert(
                "Research request failed: " +
                error.message
            );

        } finally {

            hideLoading();

        }

    }
);


// ======================================================
// CHAT MESSAGE
// ======================================================

function addChatMessage(type, text) {

    const container =
        $("chatMessages");


    const message =
        document.createElement("div");


    message.className =
        `chat-message ${type}`;


    const avatar =
        type === "user"
            ? "YOU"
            : "AI";


    const title =
        type === "user"
            ? "You"
            : "Financial Research Assistant";


    message.innerHTML = `

        <div class="avatar">
            ${avatar}
        </div>

        <div class="message">

            <strong>
                ${title}
            </strong>

            <p>
                ${escapeHTML(text)}
            </p>

        </div>

    `;


    container.appendChild(message);


    container.scrollTop =
        container.scrollHeight;

}


// ======================================================
// RESEARCH SOURCES
// ======================================================

function displaySources(sources) {

    const container =
        $("researchSources");


    if (!sources || sources.length === 0) {

        container.innerHTML =
            `<p class="empty-state">
                No sources available for this query.
            </p>`;

        return;
    }


    container.innerHTML =
        sources.map((source, index) => {

            const sourceId =
                source.source_id ||
                `S${index + 1}`;


            const filename =
                source.filename ||
                "Unknown document";


            const chunk =
                source.chunk_index !== undefined
                    ? source.chunk_index
                    : "—";


            const content =
                source.content ||
                source.document ||
                "";


            return `

                <div class="source-card">

                    <strong>
                        ${escapeHTML(sourceId)}
                        ·
                        ${escapeHTML(filename)}
                    </strong>

                    <small>
                        Chunk: ${escapeHTML(chunk)}
                    </small>

                    <p>
                        ${escapeHTML(
                            truncateText(content, 500)
                        )}
                    </p>

                </div>

            `;

        }).join("");

}


function truncateText(text, maxLength) {

    if (!text) {
        return "";
    }

    if (text.length <= maxLength) {
        return text;
    }

    return text.substring(0, maxLength) + "...";
}


// ======================================================
// COMPARISON AGENT
// ======================================================

$("comparisonForm").addEventListener(
    "submit",
    async event => {

        event.preventDefault();


        const company1 =
            $("company1").value.trim();

        const company2 =
            $("company2").value.trim();

        const query =
            $("comparisonQuery").value.trim();


        if (!company1 || !company2) {

            showAlert(
                "Please enter both company filenames."
            );

            return;
        }


        showLoading(
            "Comparing Companies",
            "Running the Comparison Agent..."
        );


        try {

            const params =
                new URLSearchParams({

                    company1: company1,

                    company2: company2,

                    query:
                        query ||
                        "Compare revenue, net income and operating income",

                    top_k: "5"

                });


            /*
             * IMPORTANT:
             * Backend /compare is POST.
             */

            const response =
                await fetch(
                    API +
                    "/compare?" +
                    params.toString(),
                    {
                        method: "POST"
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    data.message ||
                    "Comparison failed."
                );

            }


            displayComparison(data);

            showAlert(
                "Company comparison completed."
            );


        } catch (error) {

            showAlert(
                "Comparison failed: " +
                error.message
            );

        } finally {

            hideLoading();

        }

    }
);


// ======================================================
// DISPLAY COMPARISON
// ======================================================

function displayComparison(data) {

    show($("comparisonResult"));


    $("comparisonTitle").textContent =
        `${data.company1 || "Company 1"} vs ${
            data.company2 || "Company 2"
        }`;


    $("company1Header").textContent =
        data.company1 || "Company 1";


    $("company2Header").textContent =
        data.company2 || "Company 2";


    const comparison =
        data.comparison || {};


    const rows = [

        [
            "Revenue",
            comparison.revenue
        ],

        [
            "Net Income",
            comparison.net_income
        ],

        [
            "Operating Income",
            comparison.operating_income
        ]

    ];


    $("comparisonTableBody").innerHTML =
        rows.map(row => {

            const metric =
                row[1] || {};


            return `

                <tr>

                    <td>
                        ${escapeHTML(row[0])}
                    </td>

                    <td>
                        ${escapeHTML(
                            formatComparisonMetric(
                                metric.company1
                            )
                        )}
                    </td>

                    <td>
                        ${escapeHTML(
                            formatComparisonMetric(
                                metric.company2
                            )
                        )}
                    </td>

                </tr>

            `;

        }).join("");


    $("comparisonSummary").textContent =
        data.summary ||
        "No comparison summary was returned.";

}


function formatComparisonMetric(metric) {

    if (!metric) {
        return "—";
    }


    if (
        typeof metric === "string" ||
        typeof metric === "number"
    ) {

        return String(metric);

    }


    const value =
        metric.value !== undefined
            ? metric.value
            : "—";


    const unit =
        metric.unit
            ? ` ${metric.unit}`
            : "";


    return `${value}${unit}`;

}


// ======================================================
// REPORT AGENT
// ======================================================

$("reportForm").addEventListener(
    "submit",
    async event => {

        event.preventDefault();


        const companyName =
            $("reportCompany").value.trim();

        const filename =
            $("reportFilename").value.trim();


        if (!companyName || !filename) {

            showAlert(
                "Please enter company name and filename."
            );

            return;
        }


        showLoading(
            "Generating Financial Report",
            "Running Extraction, Red Flag and Report Agents..."
        );


        try {

            const params =
                new URLSearchParams({

                    company_name:
                        companyName,

                    filename:
                        filename

                });


            /*
             * IMPORTANT:
             * Backend /report is POST.
             */

            const response =
                await fetch(
                    API +
                    "/report?" +
                    params.toString(),
                    {
                        method: "POST"
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    data.message ||
                    "Report generation failed."
                );

            }


            if (data.status === "error") {

                throw new Error(
                    data.message ||
                    "Report generation failed."
                );

            }


            displayReport(data);

            showAlert(
                "Financial report generated successfully."
            );


        } catch (error) {

            showAlert(
                "Report generation failed: " +
                error.message
            );

        } finally {

            hideLoading();

        }

    }
);


// ======================================================
// DISPLAY REPORT
// ======================================================

function displayReport(data) {

    show($("reportResult"));


    const reportWrapper =
        data.report || {};


    const report =
        reportWrapper.report ||
        reportWrapper;


    $("reportTitle").textContent =
        `${reportWrapper.company || $("reportCompany").value} Financial Report`;


    $("executiveSummary").textContent =
        report.executive_summary ||
        "No executive summary was generated.";


    displayReportFinancials(
        report.key_financials || {}
    );


    displayReportRedFlags(
        report.red_flags
    );

}


function displayReportFinancials(financials) {

    const container =
        $("reportFinancials");


    const entries = [

        [
            "Revenue",
            financials.revenue
        ],

        [
            "Net Income",
            financials.net_income
        ],

        [
            "Operating Income",
            financials.operating_income
        ]

    ];


    container.innerHTML =
        entries.map(entry => {

            return `

                <div class="metric-card">

                    <span>
                        ${escapeHTML(entry[0])}
                    </span>

                    <strong>
                        ${escapeHTML(
                            formatReportMetric(
                                entry[1]
                            )
                        )}
                    </strong>

                </div>

            `;

        }).join("");

}


function formatReportMetric(value) {

    if (value === undefined || value === null) {
        return "—";
    }


    if (
        typeof value === "object" &&
        value !== null
    ) {

        if (value.value !== undefined) {

            return (
                value.value +
                (
                    value.unit
                        ? " " + value.unit
                        : ""
                )
            );

        }

        return JSON.stringify(value);
    }


    return String(value);

}


function displayReportRedFlags(flags) {

    const container =
        $("reportRedFlags");


    if (!flags || flags.length === 0) {

        container.innerHTML =
            `<div class="no-flags">
                No major financial red flags were identified
                by the current automated analysis.
            </div>`;

        return;
    }


    if (!Array.isArray(flags)) {

        container.innerHTML =
            `<div class="flag-card medium">
                <p>
                    ${escapeHTML(
                        typeof flags === "string"
                            ? flags
                            : JSON.stringify(flags)
                    )}
                </p>
            </div>`;

        return;
    }


    container.innerHTML =
        flags.map(flag => {

            if (typeof flag === "string") {

                return `
                    <div class="flag-card medium">
                        <strong>
                            Potential Indicator
                        </strong>

                        <p>
                            ${escapeHTML(flag)}
                        </p>
                    </div>
                `;

            }


            const severity =
                String(
                    flag.severity ||
                    flag.level ||
                    "Medium"
                ).toLowerCase();


            return `

                <div class="flag-card ${escapeHTML(severity)}">

                    <strong>
                        ${escapeHTML(
                            flag.title ||
                            flag.type ||
                            flag.name ||
                            "Potential Financial Indicator"
                        )}
                    </strong>

                    <p>
                        ${escapeHTML(
                            flag.description ||
                            flag.message ||
                            flag.details ||
                            flag.reason ||
                            "Potential financial indicator detected."
                        )}
                    </p>

                </div>

            `;

        }).join("");

}


// ======================================================
// INITIAL PAGE SETUP
// ======================================================

openSection("dashboard");

checkBackend();


// ======================================================
// OPTIONAL: REFRESH BACKEND STATUS
// ======================================================

setInterval(
    checkBackend,
    30000
);
