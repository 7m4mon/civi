document.getElementById('network-form').addEventListener('submit', async event => {
  event.preventDefault();
  const result = document.getElementById('network-result');
  const button = event.target.querySelector('button');
  const password = document.getElementById('network-password');
  button.disabled = true;
  result.textContent = 'Saving and applying discovery settings…';
  try {
    const bytes = new TextEncoder().encode('admin:' + password.value);
    const response = await fetch('/api/network', {method:'POST', headers:{
      Authorization:'Basic ' + btoa(String.fromCharCode(...bytes)),
      'Content-Type':'application/json', 'X-CIVI-Request':'1'},
      body:JSON.stringify({description:document.getElementById('description').value,
                          discovery:document.getElementById('discovery').checked})});
    const data = await response.json().catch(() => ({}));
    if(!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    password.value = '';
    result.textContent = data.error ? `Saved; discovery could not start: ${data.error}` :
      'Saved. Reload this page to see current discovery status.';
  } catch(error) { result.textContent = error.message; }
  finally { button.disabled = false; }
});
