import { FormEvent, useEffect, useState } from "react";
import { fetchImages, getImageUrl, uploadImage } from "./api";
import type { ImageRecord } from "./types";

function App() {
  const [images, setImages] = useState<ImageRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadImages() {
    setIsLoading(true);
    try {
      setImages(await fetchImages());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load images");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadImages();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsUploading(true);
    try {
      const form = event.currentTarget;
      await uploadImage(new FormData(form));
      form.reset();
      await loadImages();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
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
                onClick={loadImages}
                type="button"
              >
                Refresh
              </button>
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
                  <div className="space-y-2 p-4">
                    <p className="font-medium">{image.designer || "Unknown designer"}</p>
                    <p className="text-sm text-neutral-600">
                      {[image.city, image.country].filter(Boolean).join(", ") || "No location"}
                    </p>
                    {image.description ? (
                      <p className="text-sm leading-6 text-neutral-700">{image.description}</p>
                    ) : null}
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
