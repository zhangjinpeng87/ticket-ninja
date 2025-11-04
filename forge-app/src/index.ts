import Resolver from '@forge/resolver';
import { handleAnalyze, getIssueContext } from './resolvers/ai';

const resolver = new Resolver();

resolver.define('analyze', handleAnalyze);
resolver.define('getIssueContext', getIssueContext);

export const handler = resolver.getDefinitions();
