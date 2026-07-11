public class GenWhileNoUpdateBug122 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int gather(int budget, int quota) {
        int sum = 0;
        while (budget < quota) {
            sum += budget;
        }
        return sum;
    }
}
