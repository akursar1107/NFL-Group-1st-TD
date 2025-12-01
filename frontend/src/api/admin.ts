// src/api/admin.ts
export async function importData(season: number = 2025): Promise<{ success: boolean; message: string }> {
  try {
    const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}/api/import-data`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ season }),
    });
    if (!response.ok) {
      const error = await response.text();
      return { success: false, message: error };
    }
    const data = await response.json();
    return { success: true, message: data.message || 'Import successful.' };
  } catch (err: any) {
    return { success: false, message: err.message || 'Unknown error.' };
  }
}
