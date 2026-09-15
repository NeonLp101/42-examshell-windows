#include <stdlib.h>

char	*ft_itoa(int nbr)
{
	long long	n;
	int			len;
	long long	tmp;
	char		*res;

	n = nbr;
	len = (n <= 0);
	tmp = n;
	while (tmp)
	{
		tmp /= 10;
		len++;
	}
	res = malloc(len + 1);
	if (!res)
		return (NULL);
	res[len] = '\0';
	if (n < 0)
	{
		res[0] = '-';
		n = -n;
	}
	if (n == 0)
		res[0] = '0';
	while (n)
	{
		res[--len] = '0' + n % 10;
		n /= 10;
	}
	return (res);
}
