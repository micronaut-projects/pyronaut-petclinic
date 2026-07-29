const path = require('path');
const webpack = require('webpack');

module.exports = {
  entry: ['web-streams-polyfill/dist/polyfill', './frontend/server.jsx'],
  target: 'web',
  output: {
    path: path.resolve(__dirname, 'views'),
    filename: 'ssr-components.mjs',
    module: true,
    library: {type: 'module'},
    globalObject: 'globalThis'
  },
  experiments: {outputModule: true},
  module: {
    rules: [{
      test: /\.jsx?$/,
      exclude: /node_modules/,
      use: {loader: 'babel-loader'}
    }]
  },
  resolve: {extensions: ['.js', '.jsx']},
  plugins: [
    new webpack.ProvidePlugin({
      TextEncoder: ['text-encoding', 'TextEncoder'],
      TextDecoder: ['text-encoding', 'TextDecoder']
    })
  ]
};
