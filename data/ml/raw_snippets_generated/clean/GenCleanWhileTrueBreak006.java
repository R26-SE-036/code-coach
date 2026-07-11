public class GenCleanWhileTrueBreak006 {
    static int largest1(int[] weights) {
        int best = weights[0];
        for (int i = 1; i < weights.length; i++) {
            if (weights[i] > best) {
                best = weights[i];
            }
        }
        return best;
    }

    static int spin(int budget) {
        int rounds = 0;
        while (true) {
            rounds++;
            if (rounds > budget) {
                break;
            }
        }
        return rounds;
    }
}
