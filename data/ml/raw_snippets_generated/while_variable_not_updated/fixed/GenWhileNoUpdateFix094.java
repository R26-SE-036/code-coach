public class GenWhileNoUpdateFix094 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int gather(int limit, int stock) {
        int sum = 0;
        while (limit < stock) {
            sum += limit;
            limit++;
        }
        return sum;
    }

    static boolean isEven2(int budget) {
        return budget % 2 == 0;
    }
}
