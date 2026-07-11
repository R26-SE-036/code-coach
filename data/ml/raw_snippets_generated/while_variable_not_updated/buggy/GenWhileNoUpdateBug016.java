public class GenWhileNoUpdateBug016 {
    static int gather(int budget, int limit) {
        int sum = 0;
        while (budget < limit) {
            sum += budget;
        }
        return sum;
    }
}
