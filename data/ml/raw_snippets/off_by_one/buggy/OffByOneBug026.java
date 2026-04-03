package data.ml.raw_snippets.off_by_one.buggy;

public class OffByOneBug026 {
    public int[] cloneArray(int[] src) {
        int[] dest = new int[src.length];
        for (int i = 0; i <= src.length; i++) {
            dest[i] = src[i];
        }
        return dest;
    }
}
