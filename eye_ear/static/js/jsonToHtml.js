function extractHostname(url) {
  var hostname;

  if (url.indexOf("//") > -1) {
    hostname = url.split("/")[2];
  } else {
    hostname = url.split("/")[0];
  }
  hostname = hostname.split(":")[0];
  hostname = hostname.split("?")[0];

  return hostname;
}

!(function (t, e) {
  "object" == typeof exports && "undefined" != typeof module
    ? (module.exports = e())
    : "function" == typeof define && define.amd
    ? define(e)
    : ((t = t || self).edjsHTML = e());
})(this, function () {
  "use strict";
  let t = {
    delimiter: function () {
      return "<div class='ce-delimiter cdx-block'></div>";
    },
    header: function (t) {
      let e = t.data;
      return `<div class="ce-block">
      <div class="ce-block__content"><h${e.level}>${e.text}</h${e.level}></div>
      </div>`;
    },
    paragraph: function (t) {
      let alignment = t.data.alignment;
      let htmlData = `<div class="ce-block">
    <div class="ce-block__content">
      <div class="ce-paragraph cdx-block ce-paragraph--${alignment}" contenteditable="false" data-placeholder="">${t.data.text}</div>
    </div>
  </div>`;
      return htmlData;
    },
    checklist: function (t) {
      let e = t.data,
        r = "";

      return (
        e.items &&
          (r = e.items
            .map(function (t) {
              if (t.checked) {
                return (
                  "<div class='cdx-checklist__item cdx-checklist__item--checked'><span class='cdx-checklist__item-checkbox'></span><div class='cdx-checklist__item-text' contenteditable='false'>" +
                  t.text +
                  "</div></div>"
                );
              } else {
                return (
                  "<div class='cdx-checklist__item'><span class='cdx-checklist__item-checkbox'></span><div class='cdx-checklist__item-text' contenteditable='false'>" +
                  t.text +
                  "</div></div>"
                );
              }
            })
            .reduce(function (t, e) {
              return t + e;
            }, "")),
        `<div class="ce-block"><div class="ce-block__content"><div class='cdx-block cdx-checklist'>${r}</div></div></div>`
      );
    },
    list: function (t) {
      let e = t.data,
        n = "unordered" === e.style ? "ul" : "ol",
        r = "";
      return (
        e.items &&
          (r = e.items
            .map(function (t) {
              return "<li> " + t + " </li>";
            })
            .reduce(function (t, e) {
              return t + e;
            }, "")),
        `<div class="ce-block"><div class="ce-block__content"><${n}>${r}</${n}></div></div>`
      );
    },
    linkTool: function (t) {
      let e = t.data;
      let image = e.meta.image ? e.meta.image.url : "";
      let link = e.link ? e.link : "";
      let description = e.meta.description ? e.meta.description : "";
      let title = e.meta.title ? e.meta.title : "";
      let domain = extractHostname(link);

      return `<div class="ce-block"><div class="ce-block__content"><div class="link-tool"><a class="link-tool__content link-tool__content--rendered" target="_blank" ="nofollow noindex noreferrer" href="
        ${link}"><div class="link-tool__image" style="background-image: url(
          ${image}
        );"></div><div class="link-tool__title">${title}</div><p class="link-tool__description">${description}</p><span class="link-tool__anchor">${domain}</span></a></div></div></div>`;
    },
    raw: function (t) {
      let e = t.data.html;
      return (
        '<div class="ce-block"><div class="ce-block__content"><div class="cdx-block ce-rawtool raw-html">' +
        e +
        "</div></div></div>"
      );
    },
    code: function (t) {
      let e = t.data.code.replaceAll("<","&lt;").replaceAll(">","&gt;").split('\n');
      
      let htmlElement = "";
      let i;
      for(i=0;i<e.length;i++){
        htmlElement+=`<span>${e[i]}</span>`;
      }

      return (
        '<div class="ce-block"><div class="ce-block__content"><pre class="cdx-block code-block">' +
        htmlElement +
        "</pre></div></div>"
      );
    },
    table: function (t) {
      let e = t.data.content;
      let htmlData = `<div class="ce-block"><div class="ce-block__content"><div class="tc-editor cdx-block">
      <div class="tc-table__wrap">
        <table class="tc-table">
          <tbody>`;

      e.forEach((element) => {
        htmlData += "<tr>";

        element.forEach((elementdata) => {
          htmlData += `<td class="tc-table__cell">
                <div class="tc-table__area">
                  <div class="tc-table__inp" contenteditable="false">${elementdata}</div>
                </div>
              </td>`;
        });
        htmlData += "</tr>";
      });

      htmlData += `</tbody>
        </table>
        <div class="tc-toolbar--hor tc-toolbar--hidden" style="top: -11px">
          <div class="tc-toolbar__plus tc-toolbar__plus--hor">
            <svg viewBox="0 0 20 20">
              <circle cx="10" cy="10" r="10" fill="#388AE5"></circle>
              <path
                fill="#FFF"
                d="M10.9 9.1h3.7a.9.9 0 1 1 0 1.8h-3.7v3.7a.9.9 0 1 1-1.8 0v-3.7H5.4a.9.9 0 0 1 0-1.8h3.7V5.4a.9.9 0 0 1 1.8 0v3.7z"
              ></path>
            </svg>
          </div>
          <div class="tc-toolbar tc-toolbar__shine-line--hor"></div>
        </div>
        <div class="tc-toolbar--hidden tc-toolbar--ver">
          <div class="tc-toolbar__plus tc-toolbar__plus--ver">
            <svg viewBox="0 0 20 20">
              <circle cx="10" cy="10" r="10" fill="#388AE5"></circle>
              <path
                fill="#FFF"
                d="M10.9 9.1h3.7a.9.9 0 1 1 0 1.8h-3.7v3.7a.9.9 0 1 1-1.8 0v-3.7H5.4a.9.9 0 0 1 0-1.8h3.7V5.4a.9.9 0 0 1 1.8 0v3.7z"
              ></path>
            </svg>
          </div>
          <div class="tc-toolbar tc-toolbar__shine-line--ver"></div>
        </div>
      </div></div></div></div>`;
      return htmlData;
    },
    image: function (t) {
      let e = t.data,
        n = e.caption ? e.caption : "Image";

      return `<div class="ce-block ${e.stretched ? "ce-block--stretched" : ""}">
      <div class="ce-block__content">
        <div class="cdx-block image-tool image-tool--filled ${
          e.withBackground ? "image-tool--withBackground" : ""
        } ${e.withBorder ? "image-tool--withBorder" : ""}">
          <div class="image-tool__image">
            <img
              class="image-tool__image-picture"
              src="${e.file ? e.file.url : ""}"
              alt="${n}"
            />
          </div>
          ${n != "Image" ?`<div
            class="cdx-input image-tool__caption"
            contenteditable="false"
            data-placeholder="Caption"
          >
          ${n}
          </div>`:""}
        </div>
      </div>
    </div>`;
    },
    quote: function (t) {
      let e = t.data;
      return (
        '<div class="ce-block"><div class="ce-block__content"><blockquote class="cdx-block cdx-quote"><div class="cdx-input cdx-quote__text" contenteditable="false" data-placeholder="Enter a quote">' +
        e.text +
        '</div>' + 
        `${e.caption ? 
        `<div class="cdx-input cdx-quote__caption" contenteditable="false" data-placeholder="Quotes author">
        ${e.caption}
        </div>` : "" }`
        + "</blockquote></div></div>"
      );
    },
  };
  function e(t) {
    return new Error("Cannot Fetch this element");
  }
  return function (n) {
    return (
      void 0 === n && (n = {}),
      Object.assign(t, n),
      {
        parse: function (n) {
          return n.blocks.map(function (n) {
            return t[n.type] ? t[n.type](n) : e(n.type);
          });
        },
        parseBlock: function (n) {
          return t[n.type] ? t[n.type](n) : e(n.type);
        },
      }
    );
  };
});
