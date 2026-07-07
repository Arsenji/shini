export const services = [
  {
    id: 'summer',
    title: 'Летние шины',
    subtitle: 'от 4 500 ₽',
    description: 'Премиальные и бюджетные модели для тёплого сезона',
  },
  {
    id: 'winter',
    title: 'Зимние шины',
    subtitle: 'от 5 200 ₽',
    description: 'Шипованные и фрикционные — надёжное сцепление на льду',
  },
  {
    id: 'allseason',
    title: 'Всесезонные',
    subtitle: 'от 6 800 ₽',
    description: 'Универсальное решение для круглогодичной эксплуатации',
  },
  {
    id: 'disks',
    title: 'Диски',
    subtitle: 'от 3 500 ₽',
    description: 'Литые и штампованные диски под любой автомобиль',
  },
  {
    id: 'mounting',
    title: 'Шиномонтаж',
    subtitle: 'от 800 ₽',
    description: 'Монтаж, балансировка и проверка давления',
  },
  {
    id: 'storage',
    title: 'Сезонное хранение',
    subtitle: 'от 2 500 ₽',
    description: 'Контролируемые условия хранения на 6 месяцев',
  },
  {
    id: 'repair',
    title: 'Ремонт шин',
    subtitle: 'от 600 ₽',
    description: 'Грибки, вулканизация и восстановление боковин',
  },
]

export const tires = [
  {
    id: 1,
    brand: 'Michelin',
    model: 'Pilot Sport 5',
    size: '225/45 R17',
    season: 'summer' as const,
    price: 12400,
    badge: 'Хит',
  },
  {
    id: 2,
    brand: 'Nokian',
    model: 'Hakkapeliitta 10',
    size: '205/55 R16',
    season: 'winter' as const,
    price: 9800,
    badge: 'Новинка',
  },
  {
    id: 3,
    brand: 'Continental',
    model: 'PremiumContact 7',
    size: '215/60 R16',
    season: 'summer' as const,
    price: 8900,
    badge: null,
  },
  {
    id: 4,
    brand: 'Bridgestone',
    model: 'Blizzak LM005',
    size: '195/65 R15',
    season: 'winter' as const,
    price: 7200,
    badge: null,
  },
  {
    id: 5,
    brand: 'Pirelli',
    model: 'Cinturato All Season SF3',
    size: '225/50 R17',
    season: 'allseason' as const,
    price: 11200,
    badge: 'Топ',
  },
  {
    id: 6,
    brand: 'Yokohama',
    model: 'Advan Sport V107',
    size: '245/40 R18',
    season: 'summer' as const,
    price: 15800,
    badge: null,
  },
]

export const stats = [
  { value: '12 000+', label: 'комплектов продано' },
  { value: '6', label: 'брендов в наличии' },
  { value: '15 мин', label: 'среднее время монтажа' },
]

export const team = [
  {
    name: 'Козлов Андрей',
    role: 'Руководитель',
    experience: '12 лет опыта',
  },
  {
    name: 'Морозова Елена',
    role: 'Мастер шиномонтажа',
    experience: '8 лет опыта',
  },
  {
    name: 'Петров Игорь',
    role: 'Специалист по подбору',
    experience: '10 лет опыта',
  },
]

export const marqueeItems = [
  'Шины',
  'Диски',
  'Шиномонтаж',
  'Летние шины',
  'Зимние шины',
  'Балансировка',
  'Сезонное хранение',
  'Подбор по размеру',
]

export const seasonLabels: Record<string, string> = {
  summer: 'Лето',
  winter: 'Зима',
  allseason: 'Всесезон',
  all: 'Все',
}
