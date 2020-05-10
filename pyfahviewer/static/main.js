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

  /**
   * Window resize event handler.
   * @return {undefined}
   */
  function onResize() {
    // Don't resize slots while fetching
    if (!fetching) {
      let containerParent = document.getElementById("slots");
      let slotsContainer = document.querySelector(slotContainerQuery);

      // Do not attempt to resize slots if there is no slots view present.
      if (slotsContainer == null || containerParent == null) {
        return;
      }

      // To avoid screen flicker, we create a hidden clone of the slots display and force it to expanded view.
      // But we actually perform the resize on the real view. This way we don't do math on already minimized slots.
      let slotsClone = slotsContainer.cloneNode(true);
      slotsClone.style.visibility = "hidden";
      slotsClone.classList.remove("too-many-slots");
      containerParent.appendChild(slotsClone);

      let slotsWillExceedView = doSlotsExceedViewableArea(slotsClone);
      resizeSlots(slotsContainer, slotsWillExceedView);

      slotsClone.remove();
    }
  }

  /**
   * Fetches data from the API.
   * @return {undefined}
   */
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

  /**
   * Loads and renders the leaderboard data.
   * @returns {undefined}
   */
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

  /**
   * Loads and renders the slot data.
   * @returns {undefined}
   */
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

  /**
   * Renders loaded leaderboard data.
   * @param {Object} teamData Response from team data API.
   * @returns {undefined}
   */
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

    for (let i = 0; i < 15; i++) {
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

  /**
   * Renders loaded slot data.
   * @param {Object} slotData Response from slot data API.
   * @returns {undefined}
   */
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
    let slotsExceedBounds = doSlotsExceedViewableArea(slotsContainer);
    resizeSlots(slotsContainer, slotsExceedBounds);

    // If there is already a slots display, remove it.
    let containers = document.querySelectorAll(slotContainerQuery);
    if (containers.length > 1) {
      containers[0].remove();
    }

    // Display the replacement div.
    slotsContainer.style.visibility = "visible";
  }

  /**
   * Creates a new view for a particular slot.
   * @param {Object} slotData Response from the slot data API.
   * @returns {Object} An HTML element representing a single slot.
   */
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
    } else if (state === "ready" || state === "uploading" || state === "downloading") {
      slotNode.querySelector(".progress-inner").classList.add("waiting");
      percentDone = 100;
      percentCompleteText = "Retry in " + slotData.queue.nextattempt;
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

  /**
   * Determines whether slots view would exceed the viewable bounds of the slot section.
   * @param {Object} slotsInnerContainer The HTML element directly containing all of the individual slots.
   * @returns {bool} True if the slots would exceed the viewable area if rendered.
   */
  function doSlotsExceedViewableArea(slotsInnerContainer) {
    if (slotsInnerContainer === null) {
      return false;
    }

    let slotSection = document.getElementById("slots");
    let containerHeight = slotSection.clientHeight;
    let slotsHeight = slotsInnerContainer.offsetHeight;

    return slotsHeight > containerHeight;
  }

  /**
   * Switches slots to a minimal or expanded view, depending on the requireSmall parameter.
   * @param {Object} slotsInnerContainer The HTML element directly containing all of the individual slots.
   * @param {bool} requireSmall Whether the minimized view should be applied or not.
   * @returns {undefined}
   */
  function resizeSlots(slotsInnerContainer, requireSmall = false) {
    // If passed a non-existent container (window resized while still loading), do nothing.
    if (slotsInnerContainer === null) {
      return;
    }

    if (requireSmall) {
      slotsInnerContainer.classList.add("too-many-slots");
    } else {
      slotsInnerContainer.classList.remove("too-many-slots");
    }
  }

  /**
   * Formats the title of the slot.
   * CPU slots: "CPU (# of cores)"
   * GPU slots: GPU model name
   * @param {Object} slot The slot for which to format the name.
   * @returns {string} The formatted slot title.
   */
  function formatSlotName(slot) {
    if (slot.type === "cpu") {
      return slot.name + " (" + slot.cores + ")";
    }

    let re = /^(?:[^[]*\[)?([^\]]+)\]?/;
    let match = slot.name.match(re);

    return (match !== null) ? match[1] : slot.name;
  }

  /**
   * Generates an Element from an HTML string. Returns the first element in the string.
   * @param {string} html The HTML to generate an element from.
   * @returns {Object} The created HTML element.
   */
  function createElementFromHtml(html) {
    let template = document.createElement('template');
    html = html.trim();
    template.innerHTML = html;
    return template.content.firstChild;
  }
})();
