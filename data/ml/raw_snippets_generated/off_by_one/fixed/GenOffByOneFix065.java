public class GenOffByOneFix065 {
    static int addUp(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }

    static boolean isEven1(int attempts) {
        return attempts % 2 == 0;
    }
}
