const inputData = document.getElementById("inputData");
const minChangeInput = document.getElementById("minChange");
const minVolumeInput = document.getElementById("minVolume");
const scanButton = document.getElementById("scanButton");
const resultsBody = document.getElementById("results");
const summary = document.getElementById("summary");

function parseLine(line) {
  const [symbolRaw, priceRaw, changeRaw, volumeRaw] = line.split(",").map((part) => part.trim());
  const symbol = symbolRaw || "";
  const price = Number(priceRaw);
  const change = Number(changeRaw);
  const volume = Number(volumeRaw);

  const hasInvalidNumbers =
    !Number.isFinite(price) ||
    !Number.isFinite(change) ||
    !Number.isFinite(volume) ||
    price <= 0 ||
    volume < 0;

  if (!symbol || hasInvalidNumbers) {
    return null;
  }

  return { symbol: symbol.toUpperCase(), price, change, volume };
}

function renderRows(rows, minChange, minVolume) {
  resultsBody.innerHTML = "";
  let alerts = 0;

  rows.forEach((row) => {
    const isAlert = row.change >= minChange && row.volume >= minVolume;
    if (isAlert) alerts += 1;

    const tr = document.createElement("tr");
    const symbolTd = document.createElement("td");
    symbolTd.textContent = row.symbol;

    const priceTd = document.createElement("td");
    priceTd.textContent = `$${row.price.toFixed(2)}`;

    const changeTd = document.createElement("td");
    changeTd.textContent = `${row.change.toFixed(2)}%`;

    const volumeTd = document.createElement("td");
    volumeTd.textContent = row.volume.toLocaleString();

    const statusTd = document.createElement("td");
    statusTd.className = isAlert ? "status-alert" : "status-no-alert";
    statusTd.textContent = isAlert ? "ALERT" : "NO ALERT";

    tr.appendChild(symbolTd);
    tr.appendChild(priceTd);
    tr.appendChild(changeTd);
    tr.appendChild(volumeTd);
    tr.appendChild(statusTd);
    resultsBody.appendChild(tr);
  });

  summary.textContent = `Scanned ${rows.length} symbols • ${alerts} alert${alerts === 1 ? "" : "s"} found`;
}

function runScan() {
  const minChange = Number(minChangeInput.value);
  const minVolume = Number(minVolumeInput.value);

  if (Number.isNaN(minChange) || Number.isNaN(minVolume)) {
    summary.textContent = "Please enter valid numeric thresholds.";
    resultsBody.innerHTML = "";
    return;
  }

  const rows = inputData.value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map(parseLine)
    .filter(Boolean);

  renderRows(rows, minChange, minVolume);
}

scanButton.addEventListener("click", runScan);
runScan();
