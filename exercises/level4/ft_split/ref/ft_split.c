#include <stdlib.h>

static int	is_sep(char c)
{
	return (c == ' ' || c == '\t' || c == '\n');
}

char	**ft_split(char *str)
{
	char	**res;
	int		count;
	int		i;
	int		j;
	int		k;

	count = 0;
	i = 0;
	while (str[i])
	{
		if (!is_sep(str[i]) && (i == 0 || is_sep(str[i - 1])))
			count++;
		i++;
	}
	res = malloc(sizeof(char *) * (count + 1));
	if (!res)
		return (NULL);
	i = 0;
	k = 0;
	while (k < count)
	{
		while (is_sep(str[i]))
			i++;
		j = 0;
		while (str[i + j] && !is_sep(str[i + j]))
			j++;
		res[k] = malloc(j + 1);
		if (!res[k])
			return (NULL);
		res[k][j] = '\0';
		while (--j >= 0)
			res[k][j] = str[i + j];
		while (str[i] && !is_sep(str[i]))
			i++;
		k++;
	}
	res[count] = NULL;
	return (res);
}
