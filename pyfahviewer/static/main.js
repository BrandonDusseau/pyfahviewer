(function() {
  var leaderboardTemplate = null;
  var slotTemplate = null;
  var fetching = false;
  var resizeTimeout = null;
  const slotContainerQuery = ".slot-bounds";

  document.addEventListener("DOMContentLoaded", function () {
    leaderboardTemplate = document.getElementById("leader-template").content.firstElementChild;
    slotTemplate = document.getElementById("slot-template").content.firstElementChild;
    loadData();

    // Trigger resize events after the user finishes resizing.
    window.addEventListener("resize", function () {
      if (resizeTimeout) {
        clearTimeout(resizeTimeout);
      }

      resizeTimeout = setTimeout(onResize, 100);
    });

    window.setInterval(loadData, 10000);
  });

  // Window resize event handler.
  function onResize() {
    // Don't resize slots while fetching
    if (!fetching) {
      resizeSlotsIfNeeded(document.querySelector(slotContainerQuery))
    }
  }

  // Fetches data from the API.
  async function loadData() {
    if (fetching) {
      console.log("Did not fetch because a fetch is already in progress.");
      return false;
    }

    fetching = true;

    try {
      await Promise.all([
        refreshTeam(),
        refreshSlots()
      ]);
    } catch (e) {
      console.error("Unhandled exception: " + e);
    }

    fetching = false;
  }

  // Loads and renders the leaderboard data.
  async function refreshTeam() {
    let response = null;
    try {
      response = await fetch("/api/team");
    } catch (e) {
      console.error("Error when fetching team: " + e);
    }

    if (!response || !response.ok) {
      return;
    }

    let teamData = await response.json();
    renderTeamStats(teamData);
  }

  // Loads and renders the slot data.
  async function refreshSlots() {
    let response = null;
    try {
      response = await fetch("/api/slots");
    } catch (e) {
      console.error("Error when fetching slots: " + e);
    }

    if (!response || !response.ok) {
      return;
    }

    let slotData = await response.json();
    renderSlotStats(slotData);
  }

  // Renders loaded leaderboard data.
  function renderTeamStats(teamData) {
    if (teamData === null) {
      return;
    }

    if (teamData.disabled) {
      document.getElementById("leaderboard-section").classList.add("hidden");
      return;
    } else {
      document.getElementById("leaderboard-section").classList.remove("hidden");
    }

    let table = leaderboardTemplate.cloneNode(true);

    document.getElementById("team-name").innerHTML = teamData.name;
    document.getElementById("team-rank").innerHTML = "Rank: " + Number(teamData.rank).toLocaleString();
    document.getElementById("leader-header").classList.remove("hidden");

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

  // Renders loaded slot data.
  function renderSlotStats(slotData) {
    if (slotData === null) {
      return;
    }

    if (slotData.disabled) {
      document.getElementById("slots").classList.add("hidden");
      return;
    } else {
      document.getElementById("slots").classList.remove("hidden");
    }

    let slotsElement = document.getElementById("slots");

    // Create a new parent node for the slots, so that we can size it before displaying it.
    let slotsContainer = createElementFromHtml("<div class=\"slot-bounds\"></div>");
    slotsContainer.style.visibility = "hidden";

    slotData.slots.forEach(x => {
      let slotNode = generateIndividualSlot(x);
      slotsContainer.appendChild(slotNode);
    });

    // Append the replacement div to the parent.
    slotsElement.appendChild(slotsContainer);

    // If there are too many slots, show a minimal view.
    resizeSlotsIfNeeded(slotsContainer);

    // If there is already a slots display, remove it.
    let containers = document.querySelectorAll(slotContainerQuery);
    if (containers.length > 1) {
      containers[0].remove();
    }

    // Display the replacement div.
    slotsContainer.style.visibility = "visible";
  }

  // Creates a new view for a particular slot.
  function generateIndividualSlot(slotData) {
    let slotNode = slotTemplate.cloneNode(true);

    let percentCompleteText = "No work unit assigned";
    let percentDone = 0;
    let pointsDisplay = "&mdash;";

    // There may not be a queue available if a slot has no work unit assigned and is paused.
    if (slotData.queue !== null) {
      percentCompleteText = slotData.queue.percentdone + " &middot; " + slotData.queue.eta;
      percentDone = slotData.queue.percentdoneclean;
      pointsDisplay = Number(slotData.queue.creditestimate).toLocaleString();
    }

    // Note: FINISHING and READY use default styling.
    let state = slotData.status.toLowerCase();
    if (state === "paused" || state === "stopping") {
      slotNode.querySelector(".progress-inner").classList.add("paused");
    }
    else if (state === "ready" || state === "uploading" || state === "downloading") {
      slotNode.querySelector(".progress-inner").classList.add("waiting");
      percentDone = 100;
      percentCompleteText = "Waiting...";
      pointsDisplay = "&mdash;";
    }

    // Use forEach below to also fill in the value for the hidden minimized view.
    slotNode.querySelectorAll(".slot-title").forEach(
      container => container.innerHTML = formatSlotName(slotData)
    );
    slotNode.querySelectorAll(".slot-server").forEach(
      container => container.innerHTML = slotData.server
    );
    slotNode.querySelectorAll(".slot-points").forEach(
      container => container.innerHTML = pointsDisplay + " points"
    );
    slotNode.querySelectorAll(".slot-progress").forEach(
      container => container.innerHTML = percentCompleteText
    );
    slotNode.querySelectorAll(".slot-state").forEach(
      container => container.innerHTML =
        slotData.status.charAt(0).toUpperCase() + slotData.status.slice(1).toLowerCase()
    );

    slotNode.querySelector(".progress-inner").style.width = percentDone + "%";

    return slotNode;
  }

  // Switches slots to a minimal view if they would exceed the viewable bounds of the slot
  // section. If slots no longer exceed bounds, switches back.
  function resizeSlotsIfNeeded(slotsInnerContainer) {

    // If passed a non-existent container (window resized while still loading), do nothing.
    if (slotsInnerContainer === null) {
      return;
    }

    let slotSection = document.getElementById("slots");
    let containerHeight = slotSection.clientHeight;
    let slotsHeight = slotsInnerContainer.offsetHeight;

    let slotsExceedContainerBounds = slotsHeight > containerHeight;

    if (slotsExceedContainerBounds) {
      slotsInnerContainer.classList.add("too-many-slots");
    } else {
      slotsInnerContainer.classList.remove("too-many-slots");
    }
  }

  /*
   * Formats the title of the slot.
   * CPU slots: "CPU (# of cores)"
   * GPU slots: GPU model name
   */
  function formatSlotName(slot) {
    if (slot.type === "cpu") {
      return slot.name + " (" + slot.cores + ")";
    }

    let re = /^[^\[]*\[(.*)\]/;
    return slot.name.match(re)[1];
  }

  // Generates an Element from an HTML string. Returns the first element in the string.
  function createElementFromHtml(html) {
    let template = document.createElement('template');
    html = html.trim();
    template.innerHTML = html;
    return template.content.firstChild;
  }
})();
