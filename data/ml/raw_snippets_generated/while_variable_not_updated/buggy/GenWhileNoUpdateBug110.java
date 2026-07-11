public class GenWhileNoUpdateBug110 {
    static int largest1(int[] scores) {
        int best = scores[0];
        for (int i = 1; i < scores.length; i++) {
            if (scores[i] > best) {
                best = scores[i];
            }
        }
        return best;
    }

    static void pump(boolean verified, int count) {
        while (!verified) {
            System.out.println(count);
            count++;
        }
    }
}
