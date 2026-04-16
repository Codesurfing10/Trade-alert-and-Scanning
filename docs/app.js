const DEFAULT_BACKEND_URL = "https://your-render-service.onrender.com";

const backendInput = document.getElementById("backendUrl");
const symbolsInput = document.getElementById("symbols");
const resolutionInput = document.getElementById("resolution");
const lookbackDaysInput = document.getElementById("lookbackDays");
const statusText = document.getElementById("status");
const scanBtn = document.getElementById("scanBtn");
const tbody = document.querySelector("#resultsTable tbody");

backendInput.value = localStorage.getItem("backendUrl") || DEFAULT_BACKEND_URL;

const signalClass = (signal) => {
  if (signal === "L3") return "signal-l3";
  if (signal === "L2") return "signal-l2";
  if (signal === "L1") return "signal-l1";
  return "";
};

function renderRows(results) {
  tbody.innerHTML = "";
  for (const item of results) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.symbol}</td>
      <td class="${signalClass(item.signal)}">${item.signal}</td>
      <td>${item.stage2 ? "Yes" : "No"}</td>
      <td>${item.vol_ratio}</td>
      <td>${item.pct_above_fast}</td>
      <td>${item.pullback_pct}</td>
      <td>${item.breakout_bar ? "Yes" : "No"}</td>
      <td>${item.error || ""}</td>
    `;
    tbody.appendChild(tr);
  }
}

scanBtn.addEventListener("click", async () => {
  const backend = backendInput.value.trim().replace(/\/+$/, "");
  const symbols = symbolsInput.value
    .split(",")
    .map((s) => s.trim().toUpperCase())
    .filter(Boolean);
  const resolution = resolutionInput.value;
  const lookback_days = Number(lookbackDaysInput.value || 420);

  if (!backend) {
    statusText.textContent = "Please enter backend URL.";
    return;
  }
  if (!symbols.length) {
    statusText.textContent = "Please enter at least one symbol.";
    return;
  }

  localStorage.setItem("backendUrl", backend);
  statusText.textContent = "Scanning...";

  try {
    const response = await fetch(`${backend}/api/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbols, resolution, lookback_days }),
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || "Request failed");
    }
    const data = await response.json();
    renderRows(data.results || []);
    statusText.textContent = `Done. ${data.count || 0} symbols scanned.`;
  } catch (error) {
    statusText.textContent = `Error: ${error.message}`;
  }
});
