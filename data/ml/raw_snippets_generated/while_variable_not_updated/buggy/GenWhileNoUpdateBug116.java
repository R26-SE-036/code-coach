public class GenWhileNoUpdateBug116 {
    static int gather(int level, int budget) {
        int sum = 0;
        while (level < budget) {
            sum += level;
        }
        return sum;
    }
}
