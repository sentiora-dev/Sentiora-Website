const carouselTrack = document.querySelector("[data-carousel-track]");
    const carouselCards = Array.from(carouselTrack.querySelectorAll(".gallery-card"));
    const carouselPrevious = document.querySelector("[data-carousel-prev]");
    const carouselNext = document.querySelector("[data-carousel-next]");
    const carouselStatus = document.querySelector("[data-carousel-status]");
    let carouselPointerId = null;
    let carouselIsDragging = false;
    let carouselStartX = 0;
    let carouselStartScroll = 0;
    let carouselIgnoreClickUntil = 0;

    const carouselMetrics = () => {
      const cardWidth = carouselCards[0].getBoundingClientRect().width;
      const gap = Number.parseFloat(getComputedStyle(carouselTrack).columnGap) || 0;
      const step = cardWidth + gap;
      const first = Math.min(carouselCards.length - 1, Math.max(0, Math.round(carouselTrack.scrollLeft / step)));
      const visible = Math.max(1, Math.min(carouselCards.length, Math.round((carouselTrack.clientWidth + gap) / step)));
      return { step, first, visible };
    };

    const updateCarousel = () => {
      const { first, visible } = carouselMetrics();
      const last = Math.min(carouselCards.length, first + visible);
      carouselStatus.textContent = `${first + 1}–${last} / ${carouselCards.length}`;
      carouselPrevious.disabled = first === 0;
      carouselNext.disabled = last === carouselCards.length;
    };

    const moveCarousel = (direction) => {
      const { first, step } = carouselMetrics();
      const target = Math.min(carouselCards.length - 1, Math.max(0, first + direction));
      carouselTrack.scrollTo({ left: target === 0 ? 0 : target * step, behavior: "smooth" });
    };

    carouselPrevious.addEventListener("click", () => moveCarousel(-1));
    carouselNext.addEventListener("click", () => moveCarousel(1));
    carouselTrack.addEventListener("scroll", updateCarousel, { passive: true });
    window.addEventListener("resize", updateCarousel);
    carouselTrack.addEventListener("keydown", (event) => {
      if (event.key === "ArrowLeft") { event.preventDefault(); moveCarousel(-1); }
      if (event.key === "ArrowRight") { event.preventDefault(); moveCarousel(1); }
    });

    carouselTrack.addEventListener("pointerdown", (event) => {
      if (event.button !== 0) return;
      carouselPointerId = event.pointerId;
      carouselIsDragging = false;
      carouselStartX = event.clientX;
      carouselStartScroll = carouselTrack.scrollLeft;
    });

    carouselTrack.addEventListener("pointermove", (event) => {
      if (event.pointerId !== carouselPointerId) return;
      const distance = event.clientX - carouselStartX;
      if (!carouselIsDragging && Math.abs(distance) < 8) return;
      if (!carouselIsDragging) carouselTrack.setPointerCapture(event.pointerId);
      carouselIsDragging = true;
      carouselTrack.classList.add("is-dragging");
      event.preventDefault();
      carouselTrack.scrollLeft = carouselStartScroll - distance;
    });

    const finishCarouselDrag = (event) => {
      if (event.pointerId !== carouselPointerId) return;
      const dragged = carouselIsDragging;
      carouselPointerId = null;
      carouselIsDragging = false;
      carouselTrack.classList.remove("is-dragging");
      if (carouselTrack.hasPointerCapture(event.pointerId)) carouselTrack.releasePointerCapture(event.pointerId);
      if (!dragged) return;
      const { step } = carouselMetrics();
      carouselTrack.scrollTo({ left: Math.round(carouselTrack.scrollLeft / step) * step, behavior: "smooth" });
      carouselIgnoreClickUntil = performance.now() + 250;
    };

    carouselTrack.addEventListener("pointerup", finishCarouselDrag);
    carouselTrack.addEventListener("pointercancel", finishCarouselDrag);
    carouselTrack.addEventListener("click", (event) => {
      if (performance.now() >= carouselIgnoreClickUntil) return;
      event.preventDefault();
      event.stopPropagation();
    }, true);

    updateCarousel();

    const screenshotPreview = document.querySelector("#screenshot-preview");
    const screenshotPreviewImage = document.querySelector("#screenshot-preview-image");
    const screenshotPreviewTitle = document.querySelector("#screenshot-preview-title");
    const screenshotPreviewClose = document.querySelector(".screenshot-lightbox-close");
    let lastPreviewTrigger = null;

    document.querySelectorAll("[data-preview-src]").forEach((trigger) => {
      trigger.addEventListener("click", () => {
        const image = trigger.querySelector("img");
        lastPreviewTrigger = trigger;
        // The preview points at the WebP the thumbnail already downloaded, so it
        // opens instantly. Browsers too old for WebP fall back to the JPEG.
        screenshotPreviewImage.onerror = () => {
          screenshotPreviewImage.onerror = null;
          screenshotPreviewImage.src = trigger.dataset.previewSrc.replace(/\.webp$/, ".jpg");
        };
        screenshotPreviewImage.src = trigger.dataset.previewSrc;
        screenshotPreviewImage.alt = image ? image.alt : "Sentiora OpticalBurn Suite application screen";
        screenshotPreviewTitle.textContent = trigger.dataset.previewTitle || "Application preview";
        if (!screenshotPreview.open) screenshotPreview.showModal();
        screenshotPreviewClose.focus();
      });
    });

    screenshotPreviewClose.addEventListener("click", () => screenshotPreview.close());
    screenshotPreview.addEventListener("click", (event) => {
      if (event.target === screenshotPreview) screenshotPreview.close();
    });
    screenshotPreview.addEventListener("close", () => {
      screenshotPreviewImage.removeAttribute("src");
      if (lastPreviewTrigger) lastPreviewTrigger.focus();
    });
