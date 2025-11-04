import Resolver from '@forge/resolver';
import { handleAnalyze, getIssueContext, getMessages, saveMessages } from './resolvers/ai';

const resolver = new Resolver();

resolver.define('analyze', handleAnalyze);
resolver.define('getIssueContext', getIssueContext);
resolver.define('getMessages', getMessages);
resolver.define('saveMessages', saveMessages);

export const handler = resolver.getDefinitions();
