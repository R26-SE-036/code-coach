public class GenWhileNoUpdateBug096 {
    static int largest1(int[] ages) {
        int best = ages[0];
        for (int i = 1; i < ages.length; i++) {
            if (ages[i] > best) {
                best = ages[i];
            }
        }
        return best;
    }

    static int gather(int quota, int count) {
        int sum = 0;
        while (quota < count) {
            sum += quota;
        }
        return sum;
    }

    static boolean isEven2(int total) {
        return total % 2 == 0;
    }
}
