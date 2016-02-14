"use strict";

var DBG = true
var N_OF_BLINKS = 1
var confirm_btn = null
var BLINK_ANIMATION_DURATION = 400
var CONFIRM_IDLE_STATE = 0.2
var confirm_button_animation_in_progress = false
var selected_best = false
var selected_relevant = 0

var maxRelevantResults = 5

var QueryString = (function () {
	// This function is anonymous, is executed immediately and
	// the return value is assigned to QueryString!
	var query_string = {};
	var query = window.location.search.substring(1);
	var vars = query.split("&");
	for (var i=0;i<vars.length;i++) {
		var pair = vars[i].split("=");
		// If first entry with this name
		if (typeof query_string[pair[0]] === "undefined") {
			query_string[pair[0]] = pair[1];
		// If second entry with this name
		} else if (typeof query_string[pair[0]] === "string") {
			var arr = [ query_string[pair[0]], pair[1] ];
			query_string[pair[0]] = arr;
			// If third or later entry with this name
		} else {
			query_string[pair[0]].push(pair[1]);
		}
	}
	return query_string;
}());
var page_n = Math.abs(QueryString.page) || 0;

var l = function () {
	if (!DBG) {
		return
	}
	console.log.apply(console, arguments) // This is a trick to be able to pass an array of args as multiple args
}


var submit_progress = function (endpoint, data) {
	return $.ajax({
		url: '/progress/page/' + page_n + endpoint,
		type: 'PUT',
		data: data ? JSON.stringify(data) : undefined,
		contentType: "application/json"
	})
}

var animate_confirm = function () {
	CONFIRM_IDLE_STATE = 0.5 // Starting the instant we animated it at least once, we only go back to 50% instead of 20%
	if (!confirm_button_animation_in_progress) {
		confirm_button_animation_in_progress = true
		for (var i = 0; i < N_OF_BLINKS; i++) {
			confirm_btn.animate({
				opacity: CONFIRM_IDLE_STATE},
				BLINK_ANIMATION_DURATION, function() {
				confirm_btn.animate({
					opacity: 1.0},
					BLINK_ANIMATION_DURATION, function() {
					confirm_button_animation_in_progress = false
				});
			})
		}
	}
}

var animate_thank_message = function () {
	var tk = $('.thank_message')
	for (var i = 0; i < 1; i++) {
		tk.animate({
			opacity: 0.5},
			BLINK_ANIMATION_DURATION, function() {
			l("Animation complete?")
		})
		tk.animate({
			opacity: 1.0},
			BLINK_ANIMATION_DURATION, function() {
			l("Animation complete?")
		})
	}
}

var toggle_relevant = function (evt) {
	var obj = $(evt.currentTarget)
	obj.toggleClass('relevant')

	var relevantItems = obj.parent().find('.relevant')
	if (relevantItems.length > maxRelevantResults) {
		l('Max relevant reached')
		obj.removeClass('relevant')
		return false
	} else {
		update_relevant_counter(obj.parent().find('.counter') , relevantItems.length)
	}

	var isRelevant = obj.hasClass('relevant')

	submit_progress('/relevant', {
		algorithm: obj.parents('ul[data-algorithm]').data('algorithm'),
		index: obj.data('index'),
		link: obj.find('a')[0].getAttribute('href'), // @TODO can break if the structure of the snippets change.
		relevant:isRelevant
	})

	selected_relevant += (isRelevant ? 1 : -1)

	animate_confirm()
}

var on_confirm = function (evt) {
	evt.preventDefault() // The navigation will be handled by the JS

	if (!selected_best) {
		alert("Please select the best overall ranking before continuing.")
		return
	}

	if (selected_relevant <= 0) {
		if (!confirm("You have not made any relevancy judgment.\nConfirm that everything is irrelevant?")) {
			return
		}
	}

	submit_progress('/submit').then(function () {
		location.href = confirm_btn.attr('href')
	})
}

var text_size = function (evt) {
	var t = $(evt.currentTarget)
	var inc = t.hasClass('inc_ts')
	var mult = inc  ? 1 : -1

	l("Just here?")
	var s = Math.abs($('body').css('font-size').replace('px', ''))
	l("Current text size is:", s)
	s += mult * 2
	l("New text size is:", s)
	$('body').css('font-size', s)
	setCookie("ts", s, 99)
}

// from W3Cschools
function setCookie(cname, cvalue, exdays) {
	var d = new Date();
	d.setTime(d.getTime() + (exdays*24*60*60*1000));
	var expires = "expires="+d.toGMTString();
	document.cookie = cname + "=" + cvalue + "; " + expires;
}

// from W3Cschools
function getCookie(cname) {
	var name = cname + "=";
	var ca = document.cookie.split(';');
	for(var i=0; i<ca.length; i++) {
		var c = ca[i];
		while (c.charAt(0)==' ') c = c.substring(1);
		if (c.indexOf(name) != -1) return c.substring(name.length,c.length);
	}
	return "";
}

var set_text_size_from_cookie = function () {
	var s = Math.abs(getCookie("ts"))
	if (s === 0) {
		return
	}
	$('body').css('font-size', s)
}

var select_as_best = function (evt) {
	var ranking = $(evt.currentTarget).parent()

	l("element is:", ranking)

	submit_progress('/best', {
		algorithm: ranking.data('algorithm')
	}).then(function () {
		$('.serp').removeClass('relevant')
		ranking.addClass('relevant')
		selected_best = true
	})
}

var suggest_open = function (evt) {
	var so = $('.suggest_open')
	so.html(evt.currentTarget.href)
	so.get(0).href = evt.currentTarget.href
	so.css('display', 'block')
	so.css('left', evt.currentTarget.offsetLeft + 20)
	so.css('top', evt.currentTarget.offsetTop + so.height())
	return false
}

var hide_suggest_open = function (evt) {
	$('.suggest_open').css('display', 'none')
}

var update_relevant_counter = function (counter, value) {
	counter.html(value)
	if (value >= maxRelevantResults) {
		counter.addClass('max')
	} else {
		counter.removeClass('max')
	}
}

$(document).ready(function () {
	var prevNavBtn;

	// Globals
	selected_best = !! ($('.serp.relevant').length)
	selected_relevant = $('.result.relevant').length
	confirm_btn = $('#nav-next')

	// Listeners
	$('li.result a.title').click(suggest_open)
	$('li.result a.url-title').click(suggest_open)
	$('.text_size a').click(text_size)
	$('body').click(hide_suggest_open)
	$('li.result').click(toggle_relevant)
	$('.best_rank_btn').click(select_as_best)
	confirm_btn.click(on_confirm)

	// Other initialization
	$('a.help_btn').colorbox({width: 900});
	if(location.href.indexOf('#start') != -1){
		$('a.help_btn').trigger("click");
	}

	prevNavBtn = $('#nav-prev')
	if (prevNavBtn.attr('href') === '#') {
		prevNavBtn.addClass('disabled')
		prevNavBtn.click(function () {return false;})
	}

	update_relevant_counter($('.left-col .counter'), $('.left-col .relevant').length)
	update_relevant_counter($('.right-col .counter'),$('.right-col .relevant').length)

	set_text_size_from_cookie()
	animate_thank_message()
});