document.addEventListener('DOMContentLoaded', () => {
  const tabs = document.querySelectorAll('[data-login-tab]');
  if (tabs.length) {
    const building = document.getElementById('building-login');
    const city = document.getElementById('city-login');
    tabs.forEach(btn => btn.addEventListener('click', () => {
      tabs.forEach(x => x.classList.remove('active'));
      btn.classList.add('active');
      const isBuilding = btn.dataset.loginTab === 'building';
      building.hidden = !isBuilding;
      city.hidden = isBuilding;
    }));
  }
});
