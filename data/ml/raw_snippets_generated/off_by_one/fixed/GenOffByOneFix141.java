public class GenOffByOneFix141 {
    static int[] duplicate(int[] scores) {
        int[] copy = new int[scores.length];
        for (int i = 0; i < scores.length; i++) {
            copy[i] = scores[i];
        }
        return copy;
    }
}
