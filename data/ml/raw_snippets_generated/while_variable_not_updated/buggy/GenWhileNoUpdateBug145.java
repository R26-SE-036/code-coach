public class GenWhileNoUpdateBug145 {
    static int gather(int budget, int level) {
        int sum = 0;
        while (budget < level) {
            sum += budget;
        }
        return sum;
    }
}
