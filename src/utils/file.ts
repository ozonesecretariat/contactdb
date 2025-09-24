export function base64ToFile(dataURI: string, filename: string, mime: string) {
  const base64Data = dataURI.split(",")[1] || "";
  if (!base64Data) return null;

  const byteString = atob(base64Data);
  const byteArray = new Uint8Array(byteString.length);
  for (let i = 0; i < byteString.length; i += 1) {
    byteArray[i] = byteString.charCodeAt(i);
  }
  return new File([byteArray], filename, { type: mime });
}

export async function fileToBase64(file: File | null | undefined) {
  const result = await fileToBase64Dict(file);
  return result ? result.data : null;
}

export function fileToBase64Dict(file: File | null | undefined): Promise<null | { data: string; filename: string }> {
  return new Promise((resolve, reject) => {
    if (!file) {
      resolve(null);
      return;
    }

    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      resolve({
        data: reader.result as string,
        filename: file.name,
      });
    };
    reader.onerror = () => reject(new Error(`Error while reading file.`));
  });
}
