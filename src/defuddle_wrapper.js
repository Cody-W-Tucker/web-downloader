#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { JSDOM, VirtualConsole } from 'jsdom';

const VALID_FORMATS = ['html', 'markdown', 'json'];
const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));

function parseArgs(argv = process.argv.slice(2)) {
    const args = argv;
    const options = {
        url: null,
        format: 'markdown',
        property: null,
        debug: false,
        contentSelector: null,
        removeExactSelectors: true,
        removePartialSelectors: true,
        removeHiddenElements: true,
        removeLowScoring: true,
        removeSmallImages: true,
        removeImages: false,
        standardize: true,
        useAsync: true
    };

    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        switch (arg) {
            case '--url':
                if (i + 1 < args.length) options.url = args[++i];
                break;
            case '--format':
                if (i + 1 < args.length) options.format = args[++i];
                break;
            case '--property':
            case '-p':
                if (i + 1 < args.length) options.property = args[++i];
                break;
            case '--debug':
                options.debug = true;
                break;
            case '--content-selector':
                if (i + 1 < args.length) options.contentSelector = args[++i];
                break;
            // Pipeline toggles
            case '--no-remove-exact':
                options.removeExactSelectors = false;
                break;
            case '--no-remove-partial':
                options.removePartialSelectors = false;
                break;
            case '--no-remove-hidden':
                options.removeHiddenElements = false;
                break;
            case '--no-remove-low-scoring':
                options.removeLowScoring = false;
                break;
            case '--no-remove-small-images':
                options.removeSmallImages = false;
                break;
            case '--remove-images':
                options.removeImages = true;
                break;
            case '--no-standardize':
                options.standardize = false;
                break;
            case '--no-async':
                options.useAsync = false;
                break;
        }
    }

    return options;
}

async function readStdin(stdin = process.stdin) {
    return await new Promise((resolve, reject) => {
        let data = '';
        stdin.setEncoding('utf8');

        stdin.on('data', chunk => {
            data += chunk;
        });

        stdin.on('end', () => {
            resolve(data);
        });

        stdin.on('error', reject);
    });
}

function getDefuddleModuleCandidates() {
    const candidates = [];

    if (process.env.DEFUDDLE_NODE_MODULE) {
        candidates.push(process.env.DEFUDDLE_NODE_MODULE);
    }

    if (process.env.DEFUDDLE_PACKAGE_ROOT) {
        candidates.push(path.join(process.env.DEFUDDLE_PACKAGE_ROOT, 'dist', 'node.js'));
    }

    if (process.env.DEFUDDLE_NODE_MODULES) {
        candidates.push(path.join(process.env.DEFUDDLE_NODE_MODULES, 'defuddle', 'dist', 'node.js'));
    }

    candidates.push(path.resolve(SCRIPT_DIR, '..', 'node_modules', 'defuddle', 'dist', 'node.js'));
    candidates.push(path.resolve(process.cwd(), 'node_modules', 'defuddle', 'dist', 'node.js'));

    return candidates;
}

async function loadDefuddle() {
    for (const candidate of getDefuddleModuleCandidates()) {
        if (candidate && fs.existsSync(candidate)) {
            return import(pathToFileURL(candidate).href);
        }
    }

    return import('defuddle/node');
}

async function main() {
    try {
        const options = parseArgs();

        if (!options.url) {
            console.error('Error: --url is required');
            process.exit(1);
        }

        if (!VALID_FORMATS.includes(options.format)) {
            console.error(`Error: Invalid format "${options.format}". Must be one of: ${VALID_FORMATS.join(', ')}`);
            process.exit(1);
        }

        const htmlContent = await readStdin();

        if (!htmlContent || htmlContent.trim().length === 0) {
            console.error('Error: No HTML content provided');
            process.exit(1);
        }

        const dom = new JSDOM(htmlContent, {
            url: options.url,
            storageQuota: 10000000,
            virtualConsole: new VirtualConsole().sendTo(console, { omitJSDOMErrors: true })
        });

        const { Defuddle } = await loadDefuddle();

        const defuddleOptions = {
            url: options.url,
            debug: options.debug,
            markdown: options.format === 'markdown',
            removeExactSelectors: options.removeExactSelectors,
            removePartialSelectors: options.removePartialSelectors,
            removeHiddenElements: options.removeHiddenElements,
            removeLowScoring: options.removeLowScoring,
            removeSmallImages: options.removeSmallImages,
            removeImages: options.removeImages,
            standardize: options.standardize,
            useAsync: options.useAsync
        };

        if (options.contentSelector) {
            defuddleOptions.contentSelector = options.contentSelector;
        }

        const result = await Defuddle(dom, options.url, defuddleOptions);

        if (options.property) {
            if (result.hasOwnProperty(options.property)) {
                console.log(result[options.property]);
            } else {
                console.error(`Error: Property "${options.property}" not found in result`);
                console.error(`Available properties: ${Object.keys(result).join(', ')}`);
                process.exit(1);
            }
            return;
        }

        if (options.format === 'json') {
            const output = {
                success: true,
                content: result.content,
                title: result.title,
                description: result.description,
                author: result.author,
                published: result.published,
                domain: result.domain,
                site: result.site,
                language: result.language,
                wordCount: result.wordCount,
                parseTime: result.parseTime,
                favicon: result.favicon,
                image: result.image,
                metaTags: result.metaTags,
                schemaOrgData: result.schemaOrgData,
                url: options.url
            };

            if (options.debug && result.debug) {
                output.debug = result.debug;
            }

            console.log(JSON.stringify(output, null, 2));
        } else if (options.format === 'markdown') {
            console.log(result.content);
        } else {
            console.log(result.content);
        }

        process.exit(0);

    } catch (error) {
        console.error(JSON.stringify({
            success: false,
            error: error.message,
            stack: error.stack
        }, null, 2));
        process.exit(1);
    }
}

main();
