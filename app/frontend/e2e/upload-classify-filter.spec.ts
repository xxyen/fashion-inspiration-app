import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

test("uploads, classifies, searches, and filters an image", async ({ page }) => {
  const fixturePath = path.join(test.info().outputDir, "test-garment.jpg");
  fs.mkdirSync(path.dirname(fixturePath), { recursive: true });
  fs.writeFileSync(
    fixturePath,
    Buffer.from(
      "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAH/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAEFAqf/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAEDAQE/ASP/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECAQE/ASP/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAY/An//xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/IV//2gAMAwEAAgADAAAAEP/EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQMBAT8QH//EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQIBAT8QH//EABQQAQAAAAAAAAAAAAAAAAAAABD/2gAIAQEAAT8QH//Z",
      "base64"
    )
  );

  await page.goto("/");
  await page.getByLabel("Image").setInputFiles(fixturePath);
  await page.getByRole("textbox", { name: "Designer" }).fill("E2E Designer");
  await page.getByRole("textbox", { name: "Country" }).fill("France");
  await page.getByRole("textbox", { name: "City" }).fill("Paris");
  await page.getByRole("button", { name: "Upload image" }).click();

  const detailsPanel = page.getByRole("complementary");
  await expect(page.getByRole("heading", { name: "Image details" })).toBeVisible();
  await expect(detailsPanel.getByText("A fashion inspiration image pending AI classification.")).toBeVisible();
  await expect(detailsPanel.getByText("unknown", { exact: true })).toBeVisible();
  await expect(detailsPanel.getByText("inspiration", { exact: true })).toBeVisible();

  const uploadedCard = page.locator("button").filter({ hasText: "E2E Designer" });
  await page.getByPlaceholder("Search denim, embroidered, artisan market...").fill("classification placeholder");
  await expect(uploadedCard).toBeVisible();

  await page.getByLabel("Style").selectOption("inspiration");
  await expect(uploadedCard).toBeVisible();
});
