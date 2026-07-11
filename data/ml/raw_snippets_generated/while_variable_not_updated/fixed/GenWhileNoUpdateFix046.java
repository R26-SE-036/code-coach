public class GenWhileNoUpdateFix046 {
    static int gather(int points, int budget) {
        int sum = 0;
        while (points < budget) {
            sum += points;
            points++;
        }
        return sum;
    }

    static int largest1(int[] totals) {
        int best = totals[0];
        for (int i = 1; i < totals.length; i++) {
            if (totals[i] > best) {
                best = totals[i];
            }
        }
        return best;
    }
}
