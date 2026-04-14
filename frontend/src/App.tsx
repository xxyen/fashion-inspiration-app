import { FormEvent, useEffect, useState } from "react";
import {
  deleteImage,
  fetchFilters,
  fetchImages,
  getImageUrl,
  updateAnnotations,
  uploadImage
} from "./api";
import type { FilterOptions, ImageRecord } from "./types";

type GalleryFilters = {
  query: string;
  garment_type: string;
  style: string;
  material: string;
  color_palette: string;
  pattern: string;
  season: string;
  occasion: string;
  consumer_profile: string;
  country: string;
  city: string;
  designer: string;
};

const emptyFilters: GalleryFilters = {
  query: "",
  garment_type: "",
  style: "",
  material: "",
  color_palette: "",
  pattern: "",
  season: "",
  occasion: "",
  consumer_profile: "",
  country: "",
  city: "",
  designer: ""
};

const filterLabels: Record<keyof Omit<GalleryFilters, "query">, string> = {
  garment_type: "Garment type",
  style: "Style",
  material: "Material",
  color_palette: "Color",
  pattern: "Pattern",
  season: "Season",
  occasion: "Occasion",
  consumer_profile: "Consumer",
  country: "Country",
  city: "City",
  designer: "Designer"
};

const primaryFilterKeys: Array<keyof Omit<GalleryFilters, "query">> = [
  "garment_type",
  "style",
  "color_palette",
  "season",
  "country",
  "designer"
];

const advancedFilterKeys: Array<keyof Omit<GalleryFilters, "query">> = [
  "material",
  "pattern",
  "occasion",
  "consumer_profile",
  "city"
];

function App() {
  const [images, setImages] = useState<ImageRecord[]>([]);
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [filters, setFilters] = useState<GalleryFilters>(emptyFilters);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [savingAnnotationId, setSavingAnnotationId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  function imageQueryParams(nextFilters = filters) {
    const params = new URLSearchParams();
    Object.entries(nextFilters).forEach(([key, value]) => {
      if (value) {
        params.set(key, value);
      }
    });
    return params;
  }

  async function loadImages(nextFilters = filters) {
    setIsLoading(true);
    try {
      setImages(await fetchImages(imageQueryParams(nextFilters)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load images");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadImages();
    fetchFilters()
      .then(setFilterOptions)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load filters"));
  }, []);

  function updateFilter(key: keyof GalleryFilters, value: string) {
    const nextFilters = { ...filters, [key]: value };
    setFilters(nextFilters);
    loadImages(nextFilters);
  }

  function clearFilters() {
    setFilters(emptyFilters);
    loadImages(emptyFilters);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsUploading(true);
    try {
      const form = event.currentTarget;
      await uploadImage(new FormData(form));
      form.reset();
      await loadImages();
      setFilterOptions(await fetchFilters());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDelete(id: number) {
    setError(null);
    setDeletingId(id);
    try {
      await deleteImage(id);
      setImages((currentImages) => currentImages.filter((image) => image.id !== id));
      setFilterOptions(await fetchFilters());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  }

  async function handleAnnotationSubmit(event: FormEvent<HTMLFormElement>, image: ImageRecord) {
    event.preventDefault();
    setError(null);
    setSavingAnnotationId(image.id);
    try {
      const formData = new FormData(event.currentTarget);
      const tags = String(formData.get("designer_tags") ?? "")
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean);
      const notes = String(formData.get("designer_notes") ?? "").trim();
      const updated = await updateAnnotations(image.id, {
        designer_tags: tags,
        designer_notes: notes || null
      });
      setImages((currentImages) =>
        currentImages.map((currentImage) => (currentImage.id === updated.id ? updated : currentImage))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save annotations");
    } finally {
      setSavingAnnotationId(null);
    }
  }

  function metadataTags(image: ImageRecord) {
    const metadata = image.metadata;
    return [
      ...(metadata.garment_type ?? []),
      ...(metadata.style ?? []),
      ...(metadata.color_palette ?? []),
      metadata.season
    ].filter(Boolean);
  }

  function renderFilterSelect(key: keyof Omit<GalleryFilters, "query">) {
    return (
      <label className="block" key={key}>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-neutral-500">
          {filterLabels[key]}
        </span>
        <select
          className="w-full rounded-md border border-stone-300 bg-white px-3 py-2"
          onChange={(event) => updateFilter(key, event.target.value)}
          value={filters[key]}
        >
          <option value="">All</option>
          {(filterOptions?.[key] ?? []).map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
    );
  }

  return (
    <main className="min-h-screen bg-stone-50 text-neutral-900">
      <section className="mx-auto max-w-6xl px-6 py-10">
        <div className="mb-8">
          <p className="mb-2 text-sm font-semibold uppercase tracking-wide text-emerald-700">
            Fashion Inspiration App
          </p>
          <h1 className="text-4xl font-bold leading-tight sm:text-5xl">
            Upload and review field inspiration images.
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-8 text-neutral-700">
            This step stores uploaded images and shows AI metadata from the backend
            classification boundary. Search, filters, and annotations come next.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-[360px_1fr]">
          <form
            className="h-fit rounded-lg border border-stone-200 bg-white p-5 shadow-sm"
            onSubmit={handleSubmit}
          >
            <h2 className="mb-4 text-xl font-semibold">Add image</h2>

            <label className="mb-4 block">
              <span className="mb-1 block text-sm font-medium">Image</span>
              <input
                className="block w-full rounded-md border border-stone-300 bg-white px-3 py-2 text-sm"
                name="image"
                type="file"
                accept="image/*"
                required
              />
            </label>

            <label className="mb-4 block">
              <span className="mb-1 block text-sm font-medium">Designer</span>
              <input
                className="block w-full rounded-md border border-stone-300 px-3 py-2"
                name="designer"
                placeholder="Avery"
              />
            </label>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
              <label className="block">
                <span className="mb-1 block text-sm font-medium">Continent</span>
                <input
                  className="block w-full rounded-md border border-stone-300 px-3 py-2"
                  name="continent"
                  placeholder="Europe"
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-sm font-medium">Country</span>
                <input
                  className="block w-full rounded-md border border-stone-300 px-3 py-2"
                  name="country"
                  placeholder="France"
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-sm font-medium">City</span>
                <input
                  className="block w-full rounded-md border border-stone-300 px-3 py-2"
                  name="city"
                  placeholder="Paris"
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-sm font-medium">Captured at</span>
                <input
                  className="block w-full rounded-md border border-stone-300 px-3 py-2"
                  name="captured_at"
                  type="date"
                />
              </label>
            </div>

            <button
              className="mt-5 w-full rounded-md bg-neutral-900 px-4 py-3 font-semibold text-white disabled:cursor-wait disabled:opacity-60"
              disabled={isUploading}
            >
              {isUploading ? "Uploading..." : "Upload image"}
            </button>

            {error ? <p className="mt-4 text-sm text-red-700">{error}</p> : null}
          </form>

          <section>
            <div className="mb-4 flex items-end justify-between gap-4">
              <div>
                <h2 className="text-2xl font-semibold">Image library</h2>
                <p className="mt-1 text-sm text-neutral-600">
                  {isLoading ? "Loading images..." : `${images.length} image${images.length === 1 ? "" : "s"}`}
                </p>
              </div>
              <button
                className="rounded-md border border-stone-300 bg-white px-4 py-2 text-sm font-medium"
                onClick={() => loadImages()}
                type="button"
              >
                Refresh
              </button>
            </div>

            <div className="mb-5 rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
              <div className="grid gap-3 md:grid-cols-[1fr_auto]">
                <input
                  className="rounded-md border border-stone-300 px-3 py-2"
                  onChange={(event) => updateFilter("query", event.target.value)}
                  placeholder="Search denim, embroidered, artisan market..."
                  value={filters.query}
                />
                <button
                  className="rounded-md border border-stone-300 px-4 py-2 text-sm font-medium"
                  onClick={clearFilters}
                  type="button"
                >
                  Clear filters
                </button>
              </div>

              <div className="mt-4">
                <p className="mb-2 text-sm font-semibold text-neutral-700">Primary filters</p>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {primaryFilterKeys.map(renderFilterSelect)}
                </div>
              </div>

              <div className="mt-4 border-t border-stone-200 pt-4">
                <p className="mb-2 text-sm font-semibold text-neutral-700">Advanced filters</p>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {advancedFilterKeys.map(renderFilterSelect)}
                </div>
              </div>
            </div>

            {images.length === 0 && !isLoading ? (
              <div className="rounded-lg border border-dashed border-stone-300 bg-white p-8 text-center text-neutral-600">
                Upload the first inspiration image to start the library.
              </div>
            ) : null}

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {images.map((image) => (
                <article
                  className="overflow-hidden rounded-lg border border-stone-200 bg-white shadow-sm"
                  key={image.id}
                >
                  <img
                    className="aspect-[4/5] w-full object-cover"
                    src={getImageUrl(image.image_url)}
                    alt={image.description ?? "Fashion inspiration upload"}
                  />
                  <div className="space-y-3 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <p className="font-medium">{image.designer || "Unknown designer"}</p>
                      <button
                        className="rounded-md border border-red-200 px-2 py-1 text-xs font-medium text-red-700 disabled:cursor-wait disabled:opacity-60"
                        disabled={deletingId === image.id}
                        onClick={() => handleDelete(image.id)}
                        type="button"
                      >
                        {deletingId === image.id ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                    <p className="text-sm text-neutral-600">
                      {[image.city, image.country].filter(Boolean).join(", ") || "No location"}
                    </p>
                    {image.description ? (
                      <div>
                        <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                          AI description
                        </p>
                        <p className="text-sm leading-6 text-neutral-700">{image.description}</p>
                      </div>
                    ) : null}
                    <div>
                      <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                        AI metadata
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {metadataTags(image).map((tag) => (
                          <span
                            className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-800"
                            key={tag}
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="border-t border-stone-200 pt-3">
                      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                        Designer annotations
                      </p>
                      {image.designer_tags.length > 0 ? (
                        <div className="mb-2 flex flex-wrap gap-2">
                          {image.designer_tags.map((tag) => (
                            <span
                              className="rounded-full bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800"
                              key={tag}
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      ) : null}
                      {image.designer_notes ? (
                        <p className="mb-3 text-sm leading-6 text-neutral-700">{image.designer_notes}</p>
                      ) : null}
                      <form className="space-y-2" onSubmit={(event) => handleAnnotationSubmit(event, image)}>
                        <input
                          className="w-full rounded-md border border-stone-300 px-3 py-2 text-sm"
                          defaultValue={image.designer_tags.join(", ")}
                          name="designer_tags"
                          placeholder="human tags, comma separated"
                        />
                        <textarea
                          className="min-h-20 w-full rounded-md border border-stone-300 px-3 py-2 text-sm"
                          defaultValue={image.designer_notes ?? ""}
                          name="designer_notes"
                          placeholder="Designer notes and observations"
                        />
                        <button
                          className="rounded-md border border-stone-300 px-3 py-2 text-sm font-medium disabled:cursor-wait disabled:opacity-60"
                          disabled={savingAnnotationId === image.id}
                          type="submit"
                        >
                          {savingAnnotationId === image.id ? "Saving..." : "Save annotations"}
                        </button>
                      </form>
                    </div>
                    <p className="text-xs text-neutral-500">
                      Uploaded {new Date(image.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}

export default App;
