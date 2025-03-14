// Debounce function
function debounce(func, wait) {
	let timeout;
	return function (...args) {
	  const context = this;
	  clearTimeout(timeout);
	  timeout = setTimeout(() => func.apply(context, args), wait);
	};
  }
  
  // Function to get suggestions
  function getSuggestions() {
	let query = document.getElementById('search').value;
	let suggestionsDiv = document.getElementById('suggestions');
	let urlParams = new URLSearchParams(window.location.search);
	let eventId = urlParams.get("event_id");
  
	suggestionsDiv.innerHTML = '';
  
	if (query.length > 2) {
	  let apiUrl = '/autocomplete/?q=' + encodeURIComponent(query);
	  if (eventId) {
		apiUrl += '&event_id=' + encodeURIComponent(eventId);
	  }
  
	  fetch(apiUrl)
		.then(response => {
		  if (!response.ok) {
			throw new Error("HTTP error " + response.status);
		  }
		  return response.json();
		})
		.then(data => {
		  if (data.length > 0) {
			suggestionsDiv.classList.remove('hidden');
  
			let ul = document.createElement('ul');
			ul.className = "divide-y divide-gray-200";
			data.forEach(function (suggestion) {
			  let li = document.createElement('li');
			  li.className = "p-2 hover:bg-gray-100 cursor-pointer";
			  li.textContent = suggestion;
			  li.onclick = function () {
				document.getElementById('search').value = suggestion;
				suggestionsDiv.innerHTML = '';
				suggestionsDiv.classList.add('hidden');
				document.getElementById('search-form').submit();
			  };
			  ul.appendChild(li);
			});
			suggestionsDiv.appendChild(ul);
		  } else {
			suggestionsDiv.classList.add('hidden');
		  }
		})
		.catch(error => console.error('Error fetching suggestions:', error));
	} else {
	  suggestionsDiv.classList.add('hidden');
	}
  }

  async function fetchArchived(pk) {
	try {
	  const response = await fetch(`/faq/${pk}/archive`, {
		method: 'POST',
		headers: {
		  'Content-Type': 'application/json'
		}
	  });
	  const result = await response.json();
	  return result;
	} catch (error) {
	  console.error('Error archiving FAQ item:', error);
	}
  }
  
  const debouncedGetSuggestions = debounce(getSuggestions, 300);
  
  // DOMContentLoaded event to set up event listeners after the DOM is ready
  window.addEventListener('DOMContentLoaded', function () {
	const searchInput = document.getElementById('search');
	if (searchInput) {
	  searchInput.addEventListener('keyup', debouncedGetSuggestions);
	}
  
	// Mobile menu toggle
	const mobileMenuButton = document.getElementById('mobile-menu-button');
	if (mobileMenuButton) {
	  mobileMenuButton.addEventListener('click', function () {
		var menu = document.getElementById('mobile-menu');
		menu.classList.toggle('hidden');
	  });
	}
  
	// Dropdown toggle
	document.querySelectorAll('.dropdown').forEach(dropdown => {
	  dropdown.addEventListener('click', function (e) {
		e.stopPropagation();
		let menu = this.querySelector('.dropdown-menu');
		menu.classList.toggle('hidden');
	  });
	});
	
	// Close dropdowns when clicking outside
	window.addEventListener('click', function () {
	  document.querySelectorAll('.dropdown-menu').forEach(menu => {
		menu.classList.add('hidden');
	  });
	});
  
	// Scroll into view for edited FAQ item
	var editedId = "{{ edited_faq_id|default:'' }}"; // If you're templating this server-side, otherwise adjust accordingly.
	if (editedId) {
	  var el = document.getElementById("faq-" + editedId);
	  if (el) {
		el.scrollIntoView({ behavior: "smooth", block: "center" });
	  }
	}
	
	// Copy answer function (if you need to attach it to any elements later)
	window.copyAnswer = function(answerText) {
	  navigator.clipboard.writeText(answerText).then(() => {
		alert("Answer copied to clipboard!");
	  }, (err) => {
		console.error("Could not copy text: ", err);
	  });
	};
  
	// Infinite scroll for FAQ items
	let currentOffset = 200;
	const loadLimit = 200;
	let hasMoreItems = true;
	let isLoading = false;
  
	function loadMoreContent() {
	  if (!hasMoreItems || isLoading) return;
  
	  isLoading = true;
	  fetch(`/load_remaining_faqitems/?offset=${currentOffset}&limit=${loadLimit}`)
		.then(response => response.json())
		.then(data => {
		  let container = document.getElementById('faq-items-container');
  
		  data.faqitems.forEach(item => {
			let faqDiv = document.createElement('div');
			faqDiv.id = "faq-" + item.id;
			faqDiv.className = "faq-item bg-white rounded-lg shadow mb-6";
			faqDiv.innerHTML = `
			  <div class="bg-blue-600 text-white rounded-t-lg px-4 py-3">
				<h5 class="flex flew-row justify-between">
				  <span class="text-lg font-semibold">${item.question}</span> 
				  <a href="?event_id=${item.event_id}" class="text-md cursor-pointer font-normal py-1 px-4 border border-white rounded-md">
					${item.event_display_name}
				  </a>
				</h5>
			  </div>
			  <div class="px-4 py-4">
				<p class="mb-4 text-gray-800">${item.answer}</p>
			  </div>
			`;
			container.appendChild(faqDiv);
		  });
  
		  currentOffset += loadLimit;
  
		  if (!data.has_more) {
			hasMoreItems = false;
			document.getElementById('load-more-container').style.display = 'none';
		  }
		})
		.catch(error => console.error('Error loading additional FAQ items:', error))
		.finally(() => {
		  isLoading = false;
		});
	}
  
	// If there are no query params, attach scroll event listener for infinite scrolling
	if (!window.location.search) {
	  window.addEventListener('scroll', function () {
		if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 5000) {
		  loadMoreContent();
		}
	  });
	}

	const form = document.getElementById('search-form');
	form.addEventListener('submit', function(event) {
		const urlParams = new URLSearchParams(window.location.search);
		const eventId = urlParams.get('event_id');

		if (eventId) {
		let hiddenInput = document.getElementById('event-id-input');
		if (!hiddenInput) {
			hiddenInput = document.createElement('input');
			hiddenInput.type = 'hidden';
			hiddenInput.name = 'event_id';
			hiddenInput.id = 'event-id-input';
			form.appendChild(hiddenInput);
		}
		hiddenInput.value = eventId;
		}
	});
  });