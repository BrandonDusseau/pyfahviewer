(function() {
  var leaderboard_template = null;
  var slot_template = null;

  document.addEventListener("DOMContentLoaded", function () {
    leaderboard_template = document.getElementById("leader-template").content.firstElementChild;
    slot_template = document.getElementById("slot-template").content.firstElementChild;
    load_data();
  });

  function load_data() {
    host = location.protocol+'//'+location.hostname+(location.port ? ':'+location.port: '');

    // Get team stats
    fetch(host + "/api/team")
      .then((team_data) => handle_team_response(team_data));

    // Get slot stats
    fetch(host + "/api/slots")
      .then((slot_data) => handle_slot_response(slot_data))
  }

  function handle_team_response(response) {
    if (!response.ok) {
      return;
    }

    response.json().then((team_data) => render_team_stats(team_data));
  }

  function handle_slot_response(response) {
    if (!response.ok) {
      return;
    }

    response.json().then((slot_data) => render_slot_stats(slot_data));
  }

  function render_team_stats(team_data) {
    if (team_data == null) {
      return;
    }

    table = leaderboard_template.cloneNode(true);

    document.getElementById("team-name").innerHTML = team_data.name;
    document.getElementById("team-rank").innerHTML = "Rank: " + Number(team_data.rank).toLocaleString();

    for (i = 0; i < 15; i++) {
      donor = team_data.donors[i];
      table.querySelector("tbody").appendChild(create_element_from_html(
        "<tr><td>" +
        donor.name + "</td><td>" +
        Number(donor.credit).toLocaleString() + "</td><td>" +
        Number(donor.wus).toLocaleString() + "</td></tr>"
      ));
    }

    leader_container = document.getElementById("leaderboard");
    leader_container.innerHTML = "";
    leader_container.appendChild(table);
  }

  function render_slot_stats(slot_data) {
    if (slot_data == null) {
      return;
    }

    slots_element = document.getElementById("slots");

    slot_data.forEach(x => {
      slot_container = slot_template.cloneNode(true);
      slot_container.setAttribute("id", x.hash);
      slot_container.querySelector(".slot-title").innerHTML = format_slot_name(x);
      slot_container.querySelector(".slot-server").innerHTML = x.server;
      slot_container.querySelector(".slot-progress").innerHTML = x.queue.percentdone;
      slot_container.querySelector(".slot-time-remaining").innerHTML = x.queue.timeremaining;

      slots_element.appendChild(slot_container);
    });
  }

  function format_slot_name(slot) {
    if (slot.type == "cpu") {
      return slot.name + " (" + slot.cores + ")";
    }

    return slot.name;
  }

  function create_element_from_html(html) {
    var template = document.createElement('template');
    html = html.trim();
    template.innerHTML = html;
    return template.content.firstChild;
  }
})();
