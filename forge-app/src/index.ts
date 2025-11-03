import Resolver from '@forge/resolver';
import { handleAnalyze } from './resolvers/ai';

const resolver = new Resolver();

resolver.define('analyze', handleAnalyze);

export const handler = resolver.getDefinitions();
