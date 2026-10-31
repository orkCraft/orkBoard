// The probe (docs/specs/115-the-live-product-under-each-leaders-eyes.md §2.2): put first in <head> of every HTML answer of Play's proxy (gui/play_proxy.py), it tells the page that frames the
// product where it is, what is under a box, and what went wrong. Plain ES2019, no dependency, no build. It adds no element to the page and changes no style; nothing leaves the page but
// by `postMessage` to the parent, and only a message from the parent's origin is taken.
//
// The script's own address says who it is: /__ork/probe.js?o=<the parent's origin, several with commas>&p=<the play's id>. With no `o` the origin is the browser's word for the parent's
// (`location.ancestorOrigins`), else the first message the parent sends (`hello`) from `window.parent`.
//
// Every message is {ork: 1, play, kind, ...}.
//   to the parent, as they happen
//     place    {path, route, viewport: {w, h}}   at load and at every change of the history; `route` is the hash's route ("#/level/3" → "/level/3"), else ""
//     event    {event: "error", source: "error" | "rejection" | "console", message (≤ 300), stack (the first frame), page, at}
//              {event: "request", method, path (no query), host (only when it is not the page's own), status (0: no answer), ms, page, at}   never a body
//              {event: "press", selector, rect, role, pressable, dom, moved, request, changed, page, at}   sent a second after the press: whether the DOM changed, the path moved, a request began
//              (`page` is the path of the page when it happened; `at` the time in ms)
//   asked by the parent ({ork: 1, kind, id, ...}), answered with the same kind and id
//     hello / place   → place
//     under    {box: {x, y, w, h}} (CSS pixels of the frame)  → {elements: [{selector, role, text (≤ 80), rect: {x, y, w, h}, file?, line?}]} the three the box covers best; a canvas is named "canvas"
//     picture  {}                                              → {html, w, h, at} a snapshot of the document as it is now, or {none: true} when it is more than 4 MB
//     state    {}                                              → {state} what window.__ork.state() says as JSON, or {none: true} when there is none or it is more than 2 KB
(function () {
  "use strict";
  if (window.__orkProbe || window.parent === window) return;
  window.__orkProbe = true;

  var SELF = document.currentScript || document.querySelector('script[src*="/__ork/probe.js"]');
  var QUERY = new URLSearchParams(SELF && SELF.src ? SELF.src.split("?")[1] || "" : "");
  var PLAY = QUERY.get("p") || "";
  var ORIGINS = (QUERY.get("o") || "").split(",").map(function (s) { return s.trim(); }).filter(Boolean);
  if (!ORIGINS.length && window.location.ancestorOrigins && window.location.ancestorOrigins.length) ORIGINS = [window.location.ancestorOrigins[0]];
  var parentOrigin = ORIGINS.length === 1 ? ORIGINS[0] : "";   // where to post; with several (or none known) it is the one that spoke first
  var queue = [];

  var MAX_TEXT = 80, MAX_MESSAGE = 300, MAX_PICTURE = 4 * 1024 * 1024, MAX_STATE = 2048, PRESS_MS = 1000, QUEUE = 100;
  var orig = {
    pushState: history.pushState, replaceState: history.replaceState, fetch: window.fetch, open: XMLHttpRequest.prototype.open,
    send: XMLHttpRequest.prototype.send, error: console.error
  };

  // -- sending -------------------------------------------------------------------------------------------------------------------------------------------

  function post(message, origin) {
    try { window.parent.postMessage(message, origin); } catch (e) { /* the parent is gone */ }
  }

  function send(kind, data, to) {                           // `to`: the origin that asked, for an answer
    var message = Object.assign({ ork: 1, play: PLAY, kind: kind }, data);
    if (to || parentOrigin) return post(message, to || parentOrigin);
    if (queue.length < QUEUE) queue.push(message);          // the parent has not said where it is
  }

  var count = 0, windowStart = 0;
  function event(name, data) {
    var now = Date.now();                                   // a runaway loop of errors is not sent whole: 100 a second
    if (now - windowStart > 1000) { windowStart = now; count = 0; }
    if (++count > 100) return;
    send("event", Object.assign({ event: name, at: now, page: location.pathname }, data));
  }

  // -- place ---------------------------------------------------------------------------------------------------------------------------------------------

  function routeOf(hash) {
    var m = /^#!?(\/[^?]*)/.exec(hash || "");
    return m ? m[1] : "";
  }

  function pathNow() { return location.pathname + routeOf(location.hash); }

  var lastPlace = "";
  function place(force, to) {
    var data = { path: location.pathname, route: routeOf(location.hash), viewport: { w: window.innerWidth, h: window.innerHeight } };
    var key = JSON.stringify(data);
    if (!force && key === lastPlace) return;
    lastPlace = key;
    send("place", data, to);
  }

  // -- what a press brings about -------------------------------------------------------------------------------------------------------------------------

  var pressing = [];                                        // presses less than a second old: {dom, request}
  function note(what) {
    for (var i = 0; i < pressing.length; i++) pressing[i][what] = true;
  }

  function watchDom() {
    var root = document.documentElement;
    if (!root || typeof MutationObserver !== "function") return;
    new MutationObserver(function () { note("dom"); }).observe(root, { childList: true, attributes: true, characterData: true, subtree: true });
  }

  // -- naming an element ---------------------------------------------------------------------------------------------------------------------------------

  function esc(s) { return window.CSS && CSS.escape ? CSS.escape(s) : String(s).replace(/[^\w-]/g, "\\$&"); }

  function unique(selector, el) {
    try { return document.querySelectorAll(selector).length === 1 && document.querySelector(selector) === el; } catch (e) { return false; }
  }

  function selectorOf(el) {
    var parts = [], node = el;
    for (var depth = 0; node && node.nodeType === 1 && node !== document.documentElement && depth < 6; depth++) {
      var tag = node.localName, part = tag;
      var testid = node.getAttribute("data-testid");
      if (testid) { part = tag + '[data-testid="' + testid.replace(/"/g, '\\"') + '"]'; }
      else if (node.id) { part = "#" + esc(node.id); }
      else {
        var cls = (typeof node.className === "string" ? node.className : "").split(/\s+/).filter(Boolean).slice(0, 2);
        if (cls.length) part = tag + "." + cls.map(esc).join(".");
        var parent = node.parentElement;
        if (parent) {
          var same = Array.prototype.filter.call(parent.children, function (c) { return c.localName === tag; });
          if (same.length > 1) part += ":nth-of-type(" + (same.indexOf(node) + 1) + ")";
        }
      }
      parts.unshift(part);
      var selector = parts.join(" > ");
      if (unique(selector, el)) return selector;
      if (testid || node.id) break;
      node = node.parentElement;
    }
    return parts.join(" > ");
  }

  var ROLES = { a: "link", button: "button", select: "combobox", textarea: "textbox", img: "img", canvas: "canvas", nav: "navigation", main: "main", header: "banner",
    footer: "contentinfo", form: "form", ul: "list", ol: "list", li: "listitem", table: "table", dialog: "dialog", summary: "button", h1: "heading", h2: "heading",
    h3: "heading", h4: "heading", h5: "heading", h6: "heading", label: "label", video: "video", audio: "audio", svg: "graphics" };
  var INPUTS = { button: "button", submit: "button", reset: "button", checkbox: "checkbox", radio: "radio", range: "slider", search: "searchbox", number: "spinbutton" };

  function roleOf(el) {
    var role = el.getAttribute("role");
    if (role) return role;
    var tag = el.localName;
    if (tag === "input") return INPUTS[(el.getAttribute("type") || "text").toLowerCase()] || "textbox";
    if (tag === "a" && !el.hasAttribute("href")) return "";
    return ROLES[tag] || "";
  }

  var PRESSABLE = 'a[href],button,summary,input:not([type=hidden]),select,textarea,label,[role=button],[role=link],[role=tab],[role=menuitem],[role=checkbox],[role=switch],[role=option],[onclick],[tabindex]';
  function pressableOf(el) {
    var hit = el.closest ? el.closest(PRESSABLE) : null;
    if (hit) return hit;
    for (var node = el, n = 0; node && node.nodeType === 1 && n < 6; node = node.parentElement, n++) {     // what the page draws as pressable (a div with a handler)
      try { if (getComputedStyle(node).cursor === "pointer") return node; } catch (e) { return null; }
    }
    return null;
  }

  function rectOf(el) {
    var r = el.getBoundingClientRect();
    return { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) };
  }

  function textOf(el) {
    if (el.localName === "canvas") return "";
    var field = /^(input|textarea|select)$/.test(el.localName);   // what a person typed is never read, only what names the field
    var text = el.getAttribute("aria-label") || (field ? el.getAttribute("placeholder") || el.getAttribute("title") || "" :
      el.innerText || el.textContent || el.getAttribute("alt") || el.getAttribute("title") || "");
    text = String(text).replace(/\s+/g, " ").trim();
    return text.length > MAX_TEXT ? text.slice(0, MAX_TEXT - 1) + "…" : text;
  }

  // -- the source of an element's component (what the dev build tells; none is fine) -----------------------------------------------------------------------

  var SOURCE_ATTRS = ["data-source", "data-inspector-relative-path", "data-source-file", "data-component-file", "data-file", "data-vue-inspector-relative-path"];
  function splitSource(text) {
    var m = /^(.*?)(?::(\d+))?(?::(\d+))?$/.exec(String(text));
    return m && m[1] ? { file: m[1], line: m[2] ? Number(m[2]) : undefined } : null;
  }

  function sourceOf(el) {
    try {
      for (var node = el, n = 0; node && node.nodeType === 1 && n < 12; node = node.parentElement, n++) {
        for (var i = 0; i < SOURCE_ATTRS.length; i++) {
          var value = node.getAttribute(SOURCE_ATTRS[i]);
          var found = value ? splitSource(value) : null;
          if (found) {
            var line = node.getAttribute("data-inspector-line");
            if (!found.line && line && /^\d+$/.test(line)) found.line = Number(line);
            return found;
          }
        }
      }
      var key = Object.keys(el).filter(function (k) { return k.indexOf("__reactFiber$") === 0 || k.indexOf("__reactInternalInstance$") === 0; })[0];
      if (key) {                                            // React's dev build: _debugSource up to 18; the owners and parents are walked a little
        for (var fiber = el[key], hops = 0; fiber && hops < 40; fiber = fiber.return, hops++) {
          var src = fiber._debugSource || (fiber._debugOwner && fiber._debugOwner._debugSource);
          if (src && src.fileName) return { file: String(src.fileName), line: typeof src.lineNumber === "number" ? src.lineNumber : undefined };
        }
      }
      var vue = el.__vueParentComponent;                    // Vue's dev build: the component's file
      for (var hop = 0; vue && hop < 20; vue = vue.parent, hop++) {
        if (vue.type && vue.type.__file) return { file: String(vue.type.__file) };
      }
    } catch (e) { /* the dev fields are the build's, read defensively */ }
    return null;
  }

  // -- under: the elements a box covers best ------------------------------------------------------------------------------------------------------------

  function underBox(box) {
    var x = Number(box && box.x) || 0, y = Number(box && box.y) || 0, w = Math.max(0, Number(box && box.w) || 0), h = Math.max(0, Number(box && box.h) || 0);
    var seen = [], steps = w * h > 40 * 40 ? 4 : 1;         // a grid of points over the box; a press is one point
    for (var i = 0; i <= steps; i++) {
      for (var j = 0; j <= steps; j++) {
        var px = Math.min(Math.max(x + w * i / steps, 0), window.innerWidth - 1), py = Math.min(Math.max(y + h * j / steps, 0), window.innerHeight - 1);
        var stack = document.elementsFromPoint(px, py);
        for (var k = 0; k < stack.length; k++) if (seen.indexOf(stack[k]) < 0) seen.push(stack[k]);
      }
    }
    var area = (w && h) ? w * h : 1;
    var scored = seen.filter(function (el) { return el !== document.documentElement && el !== document.body; }).map(function (el) {
      var r = el.getBoundingClientRect();
      var size = r.width * r.height, inter;
      if (w && h) inter = Math.max(0, Math.min(x + w, r.right) - Math.max(x, r.left)) * Math.max(0, Math.min(y + h, r.bottom) - Math.max(y, r.top));
      else {                                                // a press, or a line: the point at its middle, so the smallest element there wins
        var cx = x + w / 2, cy = y + h / 2;
        inter = cx >= r.left && cx <= r.right && cy >= r.top && cy <= r.bottom ? Math.min(1, size) : 0;
      }
      return { el: el, score: inter / (area + size - inter || 1), size: size };   // how much of the two together they share
    }).filter(function (c) { return c.score > 0; });
    scored.sort(function (a, b) { return b.score - a.score || a.size - b.size; });
    return scored.slice(0, 3).map(function (c) {
      var item = { selector: selectorOf(c.el), role: c.el.localName === "canvas" ? "canvas" : roleOf(c.el), text: textOf(c.el), rect: rectOf(c.el) };
      var source = sourceOf(c.el);
      if (source) { item.file = source.file; if (source.line) item.line = source.line; }
      return item;
    });
  }

  // -- picture: the document as it is now ---------------------------------------------------------------------------------------------------------------

  var TEXTY = /^(text|search|email|url|tel|password|number|date|datetime-local|month|week|time)$/i;
  function mask(value) { return new Array(Math.min(String(value).length, 200) + 1).join("•"); }

  function snapshot() {
    var clone = document.documentElement.cloneNode(true);
    var live, copy, i;
    live = document.querySelectorAll("canvas"); copy = clone.querySelectorAll("canvas");
    for (i = 0; i < copy.length && i < live.length; i++) {  // a canvas is drawn into a picture of its own; a tainted one stays blank
      var img = document.createElement("img"), r = live[i].getBoundingClientRect();
      try { img.src = live[i].toDataURL("image/png"); } catch (e) { /* tainted or lost: blank */ }
      img.width = live[i].width; img.height = live[i].height;
      img.setAttribute("style", live[i].getAttribute("style") || "");
      if (!img.style.width && r.width) img.style.width = Math.round(r.width) + "px";
      if (!img.style.height && r.height) img.style.height = Math.round(r.height) + "px";
      if (live[i].className) img.className = live[i].className;
      if (live[i].id) img.id = live[i].id;
      copy[i].parentNode.replaceChild(img, copy[i]);
    }
    live = document.querySelectorAll("input"); copy = clone.querySelectorAll("input");
    for (i = 0; i < copy.length && i < live.length; i++) {
      var type = (live[i].getAttribute("type") || "text").toLowerCase();
      if (type === "checkbox" || type === "radio") { if (live[i].checked) copy[i].setAttribute("checked", ""); else copy[i].removeAttribute("checked"); }
      else if (TEXTY.test(type)) { if (live[i].value) copy[i].setAttribute("value", mask(live[i].value)); else copy[i].removeAttribute("value"); }
      else if (!/^(button|submit|reset|hidden|image)$/.test(type)) copy[i].removeAttribute("value");
    }
    live = document.querySelectorAll("textarea"); copy = clone.querySelectorAll("textarea");
    for (i = 0; i < copy.length && i < live.length; i++) copy[i].textContent = mask(live[i].value);
    live = document.querySelectorAll("style"); copy = clone.querySelectorAll("style");
    for (i = 0; i < copy.length && i < live.length; i++) {  // rules a script inserted (CSS in JS) are not in the element's text
      try {
        if (!live[i].textContent.trim() && live[i].sheet && live[i].sheet.cssRules.length) copy[i].textContent = Array.prototype.map.call(live[i].sheet.cssRules, function (rule) { return rule.cssText; }).join("\n");
      } catch (e) { /* a sheet that cannot be read */ }
    }
    Array.prototype.forEach.call(clone.querySelectorAll("script,link[rel=modulepreload],link[rel=preload]"), function (el) { el.parentNode.removeChild(el); });
    Array.prototype.forEach.call(clone.querySelectorAll("*"), function (el) {
      Array.prototype.slice.call(el.attributes).forEach(function (a) { if (/^on/i.test(a.name)) el.removeAttribute(a.name); });
    });
    var head = clone.querySelector("head");
    if (head) {                                             // the page's address, so what the snapshot names by a relative address is found where it was
      var base = clone.querySelector("base") || document.createElement("base");
      base.setAttribute("href", document.baseURI);
      if (!base.parentNode) head.insertBefore(base, head.firstChild);
    }
    var doctype = document.doctype ? "<!DOCTYPE " + document.doctype.name + ">" : "";
    return doctype + clone.outerHTML;
  }

  function picture(id, to) {
    var done = false;
    var take = function () {
      if (done) return;
      done = true;
      var reply = { id: id };
      try {
        var html = snapshot();
        var bytes = typeof TextEncoder === "function" ? new TextEncoder().encode(html).length : html.length * 3;
        if (bytes > MAX_PICTURE) reply.none = true;
        else Object.assign(reply, { html: html, w: window.innerWidth, h: window.innerHeight, at: Date.now() });
      } catch (e) { reply.none = true; }
      send("picture", reply, to);
    };
    window.requestAnimationFrame(take);                     // right after a frame, so a canvas holds what was drawn
    setTimeout(take, 400);                                  // a frame that never comes (the pane is hidden): the document as it is
  }

  // -- state: what the page chooses to tell --------------------------------------------------------------------------------------------------------------

  function state(id, to) {
    var reply = function (data) { send("state", Object.assign({ id: id }, data), to); };
    try {
      var ork = window.__ork, got = ork && typeof ork.state === "function" ? ork.state() : undefined;
      if (got === undefined) return reply({ none: true });
      var timer = new Promise(function (resolve) { setTimeout(function () { resolve(undefined); }, 500); });
      Promise.race([Promise.resolve(got), timer]).then(function (value) {
        try {
          var json = value === undefined ? undefined : JSON.stringify(value);
          if (json === undefined || json.length > MAX_STATE) return reply({ none: true });
          reply({ state: JSON.parse(json) });
        } catch (e) { reply({ none: true }); }
      }, function () { reply({ none: true }); });
    } catch (e) { reply({ none: true }); }
  }

  // -- events --------------------------------------------------------------------------------------------------------------------------------------------

  function firstFrame(stack) {
    var lines = String(stack || "").split("\n").map(function (l) { return l.trim(); }).filter(Boolean);
    var frame = lines.filter(function (l) { return /^at\s|@/.test(l) && l.indexOf("probe.js") < 0; })[0];
    return (frame || lines[0] || "").slice(0, MAX_MESSAGE);
  }

  function words(value) {
    if (value instanceof Error) return value.message || String(value);
    if (typeof value === "string") return value;
    try { return JSON.stringify(value); } catch (e) { return String(value); }
  }

  function error(source, message, stack) {
    event("error", { source: source, message: String(message).slice(0, MAX_MESSAGE), stack: firstFrame(stack) });
  }

  window.addEventListener("error", function (e) {
    if (!(e instanceof ErrorEvent)) return;                 // a resource that did not load is a request's business
    error("error", e.message || (e.error && e.error.message) || "error", (e.error && e.error.stack) || (e.filename ? "at " + e.filename + ":" + e.lineno + ":" + e.colno : ""));
  });
  window.addEventListener("unhandledrejection", function (e) {
    var why = e.reason;
    error("rejection", words(why) || "unhandled rejection", why && why.stack);
  });
  console.error = function () {
    try {
      var args = Array.prototype.slice.call(arguments);
      var first = args.filter(function (a) { return a instanceof Error; })[0];
      error("console", args.map(words).join(" "), first ? first.stack : new Error().stack);
    } catch (e) { /* never in the page's way */ }
    return orig.error.apply(console, arguments);
  };

  function request(method, url, began, status) {
    var u;
    try { u = new URL(url, location.href); } catch (e) { return; }
    if (!/^https?:$/.test(u.protocol) || u.pathname.indexOf("/__ork/") === 0) return;
    var data = { method: String(method || "GET").toUpperCase(), path: u.pathname, status: status, ms: Math.round(performance.now() - began) };
    if (u.origin !== location.origin) data.host = u.host;
    event("request", data);
  }

  if (typeof orig.fetch === "function") {
    window.fetch = function (input, init) {
      var began = performance.now();
      var method = (init && init.method) || (input && input.method) || "GET";
      var url = typeof input === "string" ? input : (input && input.url) || String(input);
      note("request");
      var promise = orig.fetch.apply(this, arguments);
      promise.then(function (res) { request(method, url, began, res.status); }, function () { request(method, url, began, 0); });
      return promise;
    };
  }
  XMLHttpRequest.prototype.open = function (method, url) {
    this.__ork = { method: method, url: url };
    return orig.open.apply(this, arguments);
  };
  XMLHttpRequest.prototype.send = function () {
    var info = this.__ork, xhr = this;
    if (info) {
      var began = performance.now();
      note("request");
      xhr.addEventListener("loadend", function () { request(info.method, info.url, began, xhr.status); });
    }
    return orig.send.apply(this, arguments);
  };

  document.addEventListener("click", function (e) {
    if (!e.isTrusted || !(e.target instanceof Element)) return;
    var hit = pressableOf(e.target), el = hit || e.target;
    var press = { dom: false, request: false }, before = pathNow();
    pressing.push(press);
    var data = { selector: selectorOf(el), rect: rectOf(el), role: roleOf(el), pressable: !!hit };
    setTimeout(function () {
      pressing.splice(pressing.indexOf(press), 1);
      var moved = pathNow() !== before;
      event("press", Object.assign(data, { dom: press.dom, moved: moved, request: press.request, changed: press.dom || moved || press.request }));
    }, PRESS_MS);
  }, true);

  // -- the parent speaks ---------------------------------------------------------------------------------------------------------------------------------

  window.addEventListener("message", function (e) {
    var m = e.data;
    if (e.source !== window.parent || !m || m.ork !== 1 || typeof m.kind !== "string") return;
    if (ORIGINS.length ? ORIGINS.indexOf(e.origin) < 0 : (parentOrigin && e.origin !== parentOrigin)) return;
    if (m.play && PLAY && m.play !== PLAY) return;
    if (!parentOrigin) {                                    // the first word of the parent says where it is
      parentOrigin = e.origin;
      var held = queue; queue = [];
      held.forEach(function (message) { post(message, parentOrigin); });
    }
    var to = e.origin, id = m.id;
    if (m.kind === "hello" || m.kind === "place") place(true, to);
    else if (m.kind === "under") {
      var reply = { id: id, elements: [] };
      try { reply.elements = underBox(m.box); } catch (err) { /* nothing under it */ }
      send("under", reply, to);
    } else if (m.kind === "picture") picture(id, to);
    else if (m.kind === "state") state(id, to);
  });

  // -- start ---------------------------------------------------------------------------------------------------------------------------------------------

  history.pushState = function () { var r = orig.pushState.apply(this, arguments); place(false); return r; };
  history.replaceState = function () { var r = orig.replaceState.apply(this, arguments); place(false); return r; };
  window.addEventListener("popstate", function () { place(false); });
  window.addEventListener("hashchange", function () { place(false); });
  if (document.documentElement) watchDom(); else document.addEventListener("DOMContentLoaded", watchDom);
  place(true);
})();
