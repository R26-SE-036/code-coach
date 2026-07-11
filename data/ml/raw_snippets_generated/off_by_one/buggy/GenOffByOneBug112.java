public class GenOffByOneBug112 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int[] duplicate(int[] scores) {
        int[] copy = new int[scores.length];
        for (int i = 0; i <= scores.length; i++) {
            copy[i] = scores[i];
        }
        return copy;
    }
}
