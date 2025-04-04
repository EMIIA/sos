addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  if (request.method === 'POST') {
    const body = await request.formData();
    const response = await fetch('https://script.google.com/macros/s/AKfycbzlQb-IiAVwMa43x_eobC3RglsjoZUueFDZGLmxyRmP0AG2A4x2Bw0q3tAZMs2CVTY/exec', {
      method: 'POST',
      body: body,
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    const result = await response.text();
    return new Response(result, { status: 200 });
  }
  return new Response('Method not allowed', { status: 405 });
}
