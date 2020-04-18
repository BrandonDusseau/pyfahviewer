(function() {
  var leaderboardTemplate = null;
  var slotTemplate = null;
  var fetching = false;

  document.addEventListener("DOMContentLoaded", function () {
    leaderboardTemplate = document.getElementById("leader-template").content.firstElementChild;
    slotTemplate = document.getElementById("slot-template").content.firstElementChild;
    loadData();

    window.setInterval(loadData, 10000);
  });

  async function loadData() {
    if (fetching) {
      console.log("Did not fetch because a fetch is already in progress.");
      return false;
    }

    fetching = true;

    await Promise.all([
      refreshTeam(),
      refreshSlots()
    ]);

    fetching = false;
  }

  async function refreshTeam() {
    let response = null;
    try {
      response = await fetch("/api/team");
    } catch (e) {
      console.log("Error when fetching team: " + e);
    }

    if (!response || !response.ok) {
      return;
    }

    let teamData = await response.json();
    renderTeamStats(teamData);
  }

  async function refreshSlots() {
    let response = null;
    try {
      response = await fetch("/api/slots");
    } catch (e) {
      console.log("Error when fetching slots: " + e);
    }

    if (!response || !response.ok) {
      return;
    }

    let slotData = await response.json();
    renderSlotStats(slotData);
  }

  function renderTeamStats(teamData) {
    if (teamData === null) {
      return;
    }

    let table = leaderboardTemplate.cloneNode(true);

    document.getElementById("team-name").innerHTML = teamData.name;
    document.getElementById("team-rank").innerHTML = "Rank: " + Number(teamData.rank).toLocaleString();

    for (i = 0; i < 15; i++) {
      let donor = teamData.donors[i];
      table.querySelector("tbody").appendChild(createElementFromHtml(
        "<tr><td class=\"overflow-el\">" +
        donor.name + "</td><td>" +
        Number(donor.credit).toLocaleString() + "</td><td>" +
        Number(donor.wus).toLocaleString() + "</td></tr>"
      ));
    }

    let leaderContainer = document.getElementById("leaderboard");
    leaderContainer.innerHTML = "";
    leaderContainer.appendChild(table);
  }

  function renderSlotStats(slotData) {
    if (slotData === null) {
      return;
    }

    let slotsElement = document.getElementById("slots");

    slotsElement.innerHTML = "";

    slotData.forEach(x => {
      let slotContainer = slotTemplate.cloneNode(true);

      let percentCompleteText = x.queue.percentdone + " &middot; " + x.queue.eta;
      let percentDone = x.queue.percentdoneclean;
      let pointsDisplay = Number(x.queue.creditestimate).toLocaleString();

      // Note: FINISHING and READY use default styling.
      let state = x.status.toLowerCase();
      if (state === "paused" || state === "stopping") {
        slotContainer.querySelector(".progress-inner").classList.add("paused");
      }
      else if (state === "ready" || state === "uploading" || state === "downloading") {
        slotContainer.querySelector(".progress-inner").classList.add("waiting");
        percentDone = 100;
        percentCompleteText = "Waiting...";
        pointsDisplay = "&mdash;";
      }

      slotContainer.setAttribute("id", x.hash);
      slotContainer.querySelector(".slot-title").innerHTML = formatSlotName(x);
      slotContainer.querySelector(".slot-server").innerHTML = x.server;
      slotContainer.querySelector(".slot-points").innerHTML = pointsDisplay + " points";
      slotContainer.querySelectorAll(".slot-progress").forEach(
        container => container.innerHTML = percentCompleteText
      );
      slotContainer.querySelector(".slot-state").innerHTML =
        x.status.charAt(0).toUpperCase() + x.status.slice(1).toLowerCase();

      slotContainer.querySelector(".progress-inner").style.width = percentDone + "%";

      slotsElement.appendChild(slotContainer);
    });
  }

  function formatSlotName(slot) {
    if (slot.type === "cpu") {
      return slot.name + " (" + slot.cores + ")";
    }

    let re = /^[^\[]*\[(.*)\]/;
    return slot.name.match(re)[1];
  }

  function createElementFromHtml(html) {
    let template = document.createElement('template');
    html = html.trim();
    template.innerHTML = html;
    return template.content.firstChild;
  }
})();
