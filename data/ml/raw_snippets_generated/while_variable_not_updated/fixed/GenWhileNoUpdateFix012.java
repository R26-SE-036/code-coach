public class GenWhileNoUpdateFix012 {
    static int largest1(int[] ages) {
        int best = ages[0];
        for (int i = 1; i < ages.length; i++) {
            if (ages[i] > best) {
                best = ages[i];
            }
        }
        return best;
    }

    static int gather(int total, int quota) {
        int sum = 0;
        while (total < quota) {
            sum += total;
            total++;
        }
        return sum;
    }
}
