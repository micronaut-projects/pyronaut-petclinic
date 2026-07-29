const path = require('path');

module.exports = {
  entry: './frontend/client.jsx',
  output: {
    path: path.resolve(__dirname, 'static'),
    filename: 'client.js'
  },
  module: {
    rules: [{
      test: /\.jsx?$/,
      exclude: /node_modules/,
      use: {loader: 'babel-loader'}
    }]
  },
  resolve: {extensions: ['.js', '.jsx']}
};
