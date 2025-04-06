import Cookies from 'js-cookie';

export const setToken = (token: string) => {
  // Set secure and HTTP-only token in production Cookies.set('token', token, { secure: process.env.NODE_ENV === 'production', sameSite: 'strict' });
  Cookies.set('token', token, { secure: false, sameSite: 'strict' });
};

export const removeToken = () => {
  Cookies.remove('token');
};
