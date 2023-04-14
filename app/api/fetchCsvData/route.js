import fs from 'fs';
import path from 'path';
import csv from 'csvtojson';
import { NextResponse } from 'next/server';

export async function GET() {
    const filePath = path.join(process.cwd(), 'backend/data/corpus_summary.csv');
    const data = await csv().fromFile(filePath);
    return NextResponse.json(data);
}