void	sort_int_tab(int *tab, unsigned int size)
{
	unsigned int	i;
	unsigned int	j;
	int				key;

	i = 1;
	while (i < size)
	{
		key = tab[i];
		j = i;
		while (j > 0 && tab[j - 1] > key)
		{
			tab[j] = tab[j - 1];
			j--;
		}
		tab[j] = key;
		i++;
	}
}
