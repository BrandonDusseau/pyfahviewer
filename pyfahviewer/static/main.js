(function() {
  const host = location.protocol+'//'+location.hostname+(location.port ? ':'+location.port: '');

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

  async function refreshTeam(response) {
    let response = await fetch(`${host}/api/team`);
    if (!response.ok) {
      return;
    }

    let teamData = await response.json();
    renderTeamStats(teamData);
  }

  async function refreshSlots(response) {
    let response = await fetch(`${host}/api/slots`);
    if (!response.ok) {
      return;
    }

    let slotData = await response.json();
    renderSlotStats(slotData);
  }

  function renderTeamStats(team_data) {
    if (team_data === null) {
      return;
    }

    let table = leaderboardTemplate.cloneNode(true);

    document.getElementById("team-name").innerHTML = team_data.name;
    document.getElementById("team-rank").innerHTML = "Rank: " + Number(team_data.rank).toLocaleString();

    for (i = 0; i < 15; i++) {
      let donor = team_data.donors[i];
      table.querySelector("tbody").appendChild(createElementFromHtml(
        "<tr><td>" +
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
      slotContainer.setAttribute("id", x.hash);
      slotContainer.querySelector(".slot-title").innerHTML = formatSlotName(x);
      slotContainer.querySelector(".slot-server").innerHTML = x.server;
      slotContainer.querySelector(".slot-progress").innerHTML =
        x.queue.percentdone + " &middot; " + x.queue.eta;
      slotContainer.querySelector(".slot-state").innerHTML =
        x.status.charAt(0).toUpperCase() + x.status.slice(1).toLowerCase();

      let state = x.status.toLowerCase();
      slotContainer.querySelector(".progress-inner").style.width = x.queue.percentdoneclean + "%";
      
      if (state == "paused") {
        slotContainer.querySelector(".progress-inner").classList.add("paused");
      }
      else if (state == "ready") {
        slotContainer.querySelector(".progress-inner").classList.add("waiting");
        slotContainer.querySelector(".progress-inner").style.width = "100%";
      }

      slotsElement.appendChild(slotContainer);
    });
  }

  function formatSlotName(slot) {
    if (slot.type == "cpu") {
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
